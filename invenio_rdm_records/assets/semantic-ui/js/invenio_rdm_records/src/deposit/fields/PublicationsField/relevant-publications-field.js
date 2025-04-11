import React from "react";
import { Button, Form, Icon, Segment } from "semantic-ui-react";
import {
  ArrayField,
  GroupField,
  TextField,
  TextAreaField
} from "react-invenio-forms";
import { i18next } from "@translations/invenio_rdm_records/i18next";

export const RelevantPublicationsField = (props) => {
  const { fieldPath, defaultValue } = props;
  return (
    <ArrayField
      addButtonLabel="Add Relevant Publications"
      defaultNewValue={defaultValue}
      fieldPath={fieldPath}
      className="additional-titles"
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        gap: '1rem'
      }}
    >
      {({ arrayHelpers, indexPath }) => {
        const fieldPathPrefix = `${fieldPath}.${indexPath}`;
        return (
          <Segment>
            <GroupField fieldPath={fieldPath} optimized style={{
              display: 'flex',
              flexDirection: 'column',
              width: '100%',
              gap: '1rem'
            }}>
              <TextField
                fieldPath={`${fieldPathPrefix}.title`}
                label="Ttitle"
                required
              />
              <TextField
                fieldPath={`${fieldPathPrefix}.doi`}
                label="DOI"
                required
              />
              <TextField
                fieldPath={`${fieldPathPrefix}.keywords`}
                label="Keywords"
                required
              />
              <TextAreaField
                fieldPath={`${fieldPathPrefix}.summary`}
                label="Summary"
                required
                fluid
              />

              <Form.Field>
                <Button color='red'
                  aria-label={i18next.t("Remove field")}
                  className="close-btn"
                  onClick={() => arrayHelpers.remove(indexPath)}

                >
                  <Icon name="close" />
                  Delete
                </Button>
              </Form.Field>
            </GroupField>
          </Segment>
        );
      }}
    </ArrayField>
  );
};
