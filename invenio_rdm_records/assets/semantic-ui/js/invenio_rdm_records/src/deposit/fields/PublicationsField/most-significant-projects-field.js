import PropTypes from "prop-types";
import React from "react";
import { Button, Form, Icon, Segment } from "semantic-ui-react";
import { ArrayField, GroupField, TextField, TextAreaField } from "react-invenio-forms";
import { i18next } from "@translations/invenio_rdm_records/i18next";

export const MostSignificantProjectsField = (props) => {
  const { fieldPath, defaultValue } = props;
  return (
    <ArrayField
      addButtonLabel="Most Significant Projects"
      defaultNewValue={defaultValue}
      fieldPath={fieldPath}
      className="additional-titles"
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        gap: "1rem",
      }}
    >
      {({ arrayHelpers, indexPath }) => {
        const fieldPathPrefix = `${fieldPath}.${indexPath}`;
        return (
          <Segment>
            <GroupField
              fieldPath={fieldPath}
              optimized
              style={{
                display: "flex",
                flexDirection: "column",
                width: "100%",
                gap: "1rem",
              }}
            >
              <TextField
                fieldPath={`${fieldPathPrefix}.title`}
                label="Project title"
                required
              />
              <TextField
                fieldPath={`${fieldPathPrefix}.institution`}
                label="Funding institution"
                required
              />
              <TextField
                fieldPath={`${fieldPathPrefix}.role`}
                label="Your role in the project"
                required
              />
              <TextAreaField
                fieldPath={`${fieldPathPrefix}.abstract`}
                label="Abstract in English"
                fluid
                required
              />
              <Form.Field>
                <Button
                  color="red"
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

MostSignificantProjectsField.propTypes = {
  fieldPath: PropTypes.string,
  defaultValue: PropTypes.string,
};
