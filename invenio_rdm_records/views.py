# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2022 Universität Hamburg.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Views."""
import logging

from flask import Blueprint

blueprint = Blueprint("invenio_rdm_records_ext", __name__)


@blueprint.record_once
def init(state):
    """Init app."""
    app = state.app
    # Register services - cannot be done in extension because
    # Invenio-Records-Resources might not have been initialized.
    sregistry = app.extensions["invenio-records-resources"].registry
    ext = app.extensions["invenio-rdm-records"]
    sregistry.register(ext.records_service, service_id="records")
    sregistry.register(ext.records_service.files, service_id="files")
    sregistry.register(ext.records_service.draft_files, service_id="draft-files")
    sregistry.register(ext.records_media_files_service, service_id="record-media-files")
    sregistry.register(ext.records_media_files_service.files, service_id="media-files")
    sregistry.register(
        ext.records_media_files_service.draft_files, service_id="draft-media-files"
    )
    sregistry.register(ext.oaipmh_server_service, service_id="oaipmh-server")
    sregistry.register(ext.iiif_service, service_id="rdm-iiif")
    # Register indexers
    iregistry = app.extensions["invenio-indexer"].registry
    iregistry.register(ext.records_service.indexer, indexer_id="records")
    iregistry.register(ext.records_service.draft_indexer, indexer_id="records-drafts")


def create_records_bp(app):
    """Create records blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.records_resource.as_blueprint()


def create_record_files_bp(app):
    """Create records files blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.record_files_resource.as_blueprint()


def create_draft_files_bp(app):
    """Create draft files blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.draft_files_resource.as_blueprint()


def create_record_media_files_bp(app):
    """Create records files blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.record_media_files_resource.as_blueprint()


def create_draft_media_files_bp(app):
    """Create draft files blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.draft_media_files_resource.as_blueprint()


def create_parent_record_links_bp(app):
    """Create parent record links blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.parent_record_links_resource.as_blueprint()


def create_parent_grants_bp(app):
    """Create record grants blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.parent_grants_resource.as_blueprint()


def create_pid_resolver_resource_bp(app):
    """Create pid resource blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.pid_resolver_resource.as_blueprint()


def create_community_records_bp(app):
    """Create community's records blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.community_records_resource.as_blueprint()


def create_person_records_bp(app):
    """Create person's records blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.person_records_resource.as_blueprint()


def create_organization_records_bp(app):
    """Create organization's records blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.organization_records_resource.as_blueprint()


def create_record_communities_bp(app):
    """Create record communities blueprint."""
    return app.extensions[
        "invenio-rdm-records"
    ].record_communities_resource.as_blueprint()


def create_record_requests_bp(app):
    """Create record communities blueprint."""
    return app.extensions["invenio-rdm-records"].record_requests_resource.as_blueprint()


def create_oaipmh_server_blueprint_from_app(app):
    """Create app blueprint."""
    return app.extensions["invenio-rdm-records"].oaipmh_server_resource.as_blueprint()


def create_iiif_bp(app):
    """Create IIIF blueprint."""
    ext = app.extensions["invenio-rdm-records"]
    return ext.iiif_resource.as_blueprint()
