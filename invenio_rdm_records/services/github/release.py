# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2024 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Github release API implementation."""

from flask import current_app
from invenio_access.permissions import authenticated_user, system_identity
from invenio_access.utils import get_identity
from invenio_db import db
from invenio_github.api import GitHubRelease
from invenio_github.models import ReleaseStatus
from invenio_records_resources.services.uow import UnitOfWork

from ...proxies import current_rdm_records_service
from ...resources.serializers.ui import UIJSONSerializer
from ..errors import RecordDeletedException
from .metadata import RDMReleaseMetadata
from .utils import retrieve_recid_by_uuid


def _get_user_identity(user):
    """Get user identity."""
    identity = get_identity(user)
    identity.provides.add(authenticated_user)
    return identity


class RDMGithubRelease(GitHubRelease):
    """Implement release API instance for RDM."""

    metadata_cls = RDMReleaseMetadata

    @property
    def metadata(self):
        """Extracts metadata to create an RDM draft."""
        metadata = self.metadata_cls(self)
        output = metadata.default_metadata
        output.update(metadata.extra_metadata)
        output.update(metadata.citation_metadata)

        if not output.get("creators"):
            # Get owner from Github API
            owner = self.get_owner()
            if owner:
                output.update({"creators": [owner]})

        # Default to "Unkwnown"
        if not output.get("creators"):
            output.update(
                {
                    "creators": [
                        {
                            "person_or_org": {
                                "type": "personal",
                                "family_name": "Unknown",
                            },
                        }
                    ]
                }
            )

        # Add default license if not yet added
        if not output.get("rights"):
            default_license = "cc-by-4.0"
            if metadata.repo_license:
                default_license = metadata.repo_license.lower()
            output.update({"rights": [{"id": default_license}]})
        return output

    def get_custom_fields(self):
        """Get custom fields."""
        ret = {}
        repo_url = self.repository_payload["html_url"]
        ret["code:codeRepository"] = repo_url
        return ret

    def get_owner(self):
        """Retrieves repository owner and its affiliation, if any."""
        # `owner.name` is not required, `owner.login` is.
        output = None
        if self.owner:
            name = getattr(self.owner, "name", self.owner.login)
            company = getattr(self.owner, "company", None)
            output = {"person_or_org": {"type": "personal", "family_name": name}}
            if company:
                output.update({"affiliations": [{"name": company}]})
        return output

    def resolve_record(self):
        """Resolves an RDM record from a release."""
        if not self.release_object.record_id:
            return None
        recid = retrieve_recid_by_uuid(self.release_object.record_id)
        try:
            return current_rdm_records_service.read(system_identity, recid.pid_value)
        except RecordDeletedException:
            return None

    def _upload_files_to_draft(self, identity, draft, uow):
        """Upload files to draft."""
        # Validate the release files are fetchable
        self.test_zipball()

        draft_file_service = current_rdm_records_service.draft_files

        draft_file_service.init_files(
            identity,
            draft.id,
            data=[{"key": self.release_file_name}],
            uow=uow,
        )

        with self.fetch_zipball_file() as file_stream:
            draft_file_service.set_file_content(
                identity,
                draft.id,
                self.release_file_name,
                file_stream,
                uow=uow,
            )

    def publish(self):
        """Publish GitHub release as record.

        Drafts and records are created using the current records service.
        The following steps are run inside a single transaction:

        - Create a draft.
        - The draft's ownership is set to the user's id via its parent.
        - Upload files to the draft.
        - Publish the draft.

        In case of failure, the transaction is rolled back and the release status set to 'FAILED'

        :raises ex: any exception generated by the records service (e.g. invalid metadata)
        """
        try:
            self.release_processing()
            # Commit state change, in case the publishing is stuck
            db.session.commit()

            draft_file_service = current_rdm_records_service.draft_files

            with UnitOfWork(db.session) as uow:
                data = {
                    "metadata": self.metadata,
                    "access": {"record": "public", "files": "public"},
                    "files": {"enabled": True},
                    "custom_fields": self.get_custom_fields(),
                }
                if self.is_first_release():
                    # For the first release, use the repo's owner identity.
                    identity = self.user_identity
                    draft = current_rdm_records_service.create(identity, data, uow=uow)
                    self._upload_files_to_draft(identity, draft, uow)
                else:
                    # Retrieve latest record id and its recid
                    latest_record_uuid = self.repository_object.latest_release(
                        ReleaseStatus.PUBLISHED
                    ).record_id

                    recid = retrieve_recid_by_uuid(latest_record_uuid)

                    # Use the previous record's owner as the new version owner
                    last_record = current_rdm_records_service.read(
                        system_identity, recid.pid_value, include_deleted=True
                    )
                    owner = last_record._record.parent.access.owner.resolve()

                    identity = _get_user_identity(owner)

                    # Create a new version and update its contents
                    new_version_draft = current_rdm_records_service.new_version(
                        identity, recid.pid_value, uow=uow
                    )

                    self._upload_files_to_draft(identity, new_version_draft, uow)

                    draft = current_rdm_records_service.update_draft(
                        identity, new_version_draft.id, data, uow=uow
                    )

                draft_file_service.commit_file(
                    identity, draft.id, self.release_file_name, uow=uow
                )

                record = current_rdm_records_service.publish(
                    identity, draft.id, uow=uow
                )

                # Update release weak reference and set status to PUBLISHED
                self.release_object.record_id = record._record.model.id
                self.release_published()

                # UOW must be committed manually since we're not using the decorator
                uow.commit()
                return record
        except Exception as ex:
            # Flag release as FAILED and raise the exception
            self.release_failed()
            # Commit the FAILED state, other changes were already rollbacked by the UOW
            db.session.commit()
            raise ex

    def process_release(self):
        """Processes a github release.

        The release might be first validated, in terms of sender, and then published.

        :raises ex: any exception generated by the records service when creating a draft or publishing the release record.
        """
        try:
            record = self.publish()
            return record
        except Exception as ex:
            current_app.logger.exception(
                f"Error while processing GitHub release {self.release_object.id}: {str(ex)}"
            )
            raise ex

    def serialize_record(self):
        """Serializes an RDM record."""
        return UIJSONSerializer().serialize_object(self.record.data)

    @property
    def record_url(self):
        """Release self url points to RDM record.

        It points to DataCite URL if the integration is enabled, otherwise it points to the HTML URL.
        """
        html_url = self.record.data["links"]["self_html"]
        doi_url = self.record.data["links"].get("doi")
        return doi_url or html_url

    @property
    def badge_title(self):
        """Returns the badge title."""
        if current_app.config.get("DATACITE_ENABLED"):
            return "DOI"

    @property
    def badge_value(self):
        """Returns the badge value."""
        if current_app.config.get("DATACITE_ENABLED"):
            return self.record.data.get("pids", {}).get("doi", {}).get("identifier")
