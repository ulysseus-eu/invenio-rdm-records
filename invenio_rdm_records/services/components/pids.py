# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Graz University of Technology.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RDM service component for PIDs."""

from copy import copy

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_records_resources.services.uow import TaskOp

from ..pids.tasks import register_or_update_pid


class PIDsComponent(ServiceComponent):
    """Service component for PIDs."""

    def create(self, identity, data=None, record=None, errors=None):
        """This method is called on draft creation.

        It validates and add the pids to the draft.
        """
        pids_data = record.pids or {}  # current pids state
        if "pids" in data:  # there is new input data for PIDs
            pids_data = data["pids"]

        self.service.pids.pid_manager.validate(pids_data, record, errors)
        record.pids = pids_data

    def update_draft(self, identity, data=None, record=None, errors=None):
        """Update draft handler."""
        pids_data = record.pids or {}  # current pids state
        if "pids" in data:  # there is new input data for PIDs
            pids_data = data["pids"]

        self.service.pids.pid_manager.validate(pids_data, record, errors)
        record.pids = pids_data

    def delete_draft(self, identity, draft=None, record=None, force=False):
        """This method deletes PIDs of a draft.

        It should only delete PIDs with status `NEW`, as other PIDs would
        belong to previous versions of the record.
        """
        # ATTENTION: Delete draft is called both for published and unpublished
        # records. Hence, we cannot just delete all PIDs, but only the new
        # unregistered PIDs.
        to_remove = copy(draft.get("pids", {}))
        record_pids = record.get("pids", {}).keys() if record else []
        for scheme in record_pids:
            to_remove.pop(scheme)

        self.service.pids.pid_manager.discard_all(to_remove)
        draft.pids = {}

    def publish(self, identity, draft=None, record=None):
        """Publish handler."""
        # ATTENTION: A draft can be for both an unpublished or published
        # record. For an unpublished record, we usually simply need to create
        # and reserve all PIDs. For a published record, some PIDs may allow
        # changes.

        # Extract all PIDs/schemes from the draft and the record
        draft_pids = draft.get("pids", {})
        record_pids = copy(record.get("pids", {}))
        draft_schemes = set(draft_pids.keys())
        record_schemes = set(record_pids.keys())
        required_schemes = set(self.service.config.pids_required)

        # Validate the draft PIDs
        self.service.pids.pid_manager.validate(draft_pids, draft, raise_errors=True)

        # Detect which PIDs on a published record that has been changed.
        #
        # Example: An external DOI (i.e. DOI not managed by us) can be changed
        # on a published record. Changes are handled by removing the old PID
        # and adding the new.
        changed_pids = {}
        for scheme in draft_schemes & record_schemes:
            record_id = record_pids[scheme]["identifier"]
            draft_id = draft_pids[scheme]["identifier"]
            if record_id != draft_id:
                changed_pids[scheme] = record_pids[scheme]

        self.service.pids.pid_manager.validate_restriction_level(draft)

        self.service.pids.pid_manager.discard_all(changed_pids)

        # Determine schemes which are required, but not yet created.
        missing_required_schemes = required_schemes - record_schemes - draft_schemes
        # Create all PIDs specified on draft and all missing required PIDs
        pids = self.service.pids.pid_manager.create_all(
            draft,
            pids=draft_pids,
            schemes=(
                missing_required_schemes
                if draft["access"]["record"] != "restricted"
                else None
            ),
        )

        # Reserve all created PIDs and store them on the record
        self.service.pids.pid_manager.reserve_all(draft, pids)

        # Restore any removed required PIDs
        removed_required_pids = (record_schemes - draft_schemes) & required_schemes
        pids.update(
            {
                scheme: record_pids[scheme]
                for scheme in removed_required_pids
                if scheme in record_pids
            }
        )

        # Set the resulting PIDs on the record
        record.pids = pids

        # Async register/update tasks after transaction commit.
        for scheme in pids.keys():
            self.uow.register(TaskOp(register_or_update_pid, record["id"], scheme))

    def new_version(self, identity, draft=None, record=None):
        """A new draft should not have any pids from the previous record."""
        # This makes the draft use the same identifier as the previous
        # version
        if record.pids.get("doi", {}).get("provider") == "external":
            draft.pids = {"doi": {"provider": "external", "identifier": ""}}
        else:
            draft.pids = {}

    def edit(self, identity, draft=None, record=None):
        """Add current pids from the record to the draft.

        PIDs are taken from the published record so that they cannot be changed
        in the draft.
        """
        pids = record.get("pids", {})
        self.service.pids.pid_manager.validate(pids, record)
        draft.pids = pids

    def delete_record(self, identity, data=None, record=None, uow=None):
        """Process pids on delete record."""
        record_pids = copy(record.get("pids", {}))
        self.service.pids.pid_manager.discard_all(record_pids, soft_delete=True)

    def restore_record(self, identity, record=None, uow=None):
        """Restore previously invalidated pids."""
        record_pids = copy(record.get("pids", {}))
        self.service.pids.pid_manager.restore_all(record_pids)


class ParentPIDsComponent(ServiceComponent):
    """Service component for record parent PIDs."""

    def create(self, identity, data=None, record=None, errors=None):
        """This method is called on draft creation."""
        record.parent.pids = {}

    def publish(self, identity, draft=None, record=None):
        """Publish handler."""
        # Extract all current PIDs/schemes from the parent record. These are coming from
        # previously published record versions.
        current_pids = copy(record.parent.get("pids", {}))
        current_schemes = set(current_pids.keys())
        required_schemes = set(self.service.config.parent_pids_required)

        conditional_schemes = self.service.config.parent_pids_conditional
        for scheme in set(required_schemes):
            condition_func = conditional_schemes.get(scheme)
            if condition_func and not condition_func(record):
                required_schemes.remove(scheme)

        # TODO: Maybe here we can check so that we don't create a Concept DOI for
        #       already published records that don't have one (i.e. legacy records).
        # Create all missing PIDs (this happens only on first publish)
        missing_required_schemes = required_schemes - current_schemes
        pids = self.service.pids.parent_pid_manager.create_all(
            record.parent,
            pids=current_pids,
            schemes=missing_required_schemes,
        )
        # Reserve all created PIDs and store them on the parent record
        self.service.pids.parent_pid_manager.reserve_all(record.parent, pids)
        record.parent.pids = pids

        # TODO: This should normally be done in `Service.publish`
        self.uow.register(
            ParentRecordCommitOp(
                record.parent, indexer_context=dict(service=self.service)
            )
        )

        # Async register/update tasks after transaction commit.
        for scheme in pids.keys():
            self.uow.register(
                TaskOp(register_or_update_pid, record["id"], scheme, parent=True)
            )

    def delete_record(self, identity, data=None, record=None, uow=None):
        """Process pids on delete record."""
        record_cls = self.service.record_cls
        parent_pids = copy(record.parent.get("pids", {}))
        if record_cls.next_latest_published_record_by_parent(record.parent) is None:
            self.service.pids.parent_pid_manager.discard_all(
                parent_pids, soft_delete=True
            )

        # Async register/update tasks after transaction commit.
        for scheme in parent_pids.keys():
            self.uow.register(
                TaskOp(register_or_update_pid, record["id"], scheme, parent=True)
            )

    def restore_record(self, identity, record=None, uow=None):
        """Restore previously invalidated pids."""
        parent_pids = copy(record.parent.get("pids", {}))
        self.service.pids.parent_pid_manager.restore_all(parent_pids)

        # Async register/update tasks after transaction commit.
        for scheme in parent_pids.keys():
            self.uow.register(
                TaskOp(register_or_update_pid, record["id"], scheme, parent=True)
            )
