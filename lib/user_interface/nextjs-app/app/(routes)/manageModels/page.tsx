"use client";

import "@aws-amplify/ui-react/styles.css";
import {
  Box,
  Button,
  ContentLayout,
  Header,
  SpaceBetween,
  Table,
  TextFilter,
} from "@cloudscape-design/components";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ModelStatus } from "../../API";
import withAuth from "../../components/auth/withAuth";
import ModelUploadButton from "../../components/chatbot/ModelUploadButton";
import { useLayoutContext } from "../../contexts/layoutcontext";
import { useModels } from "../../hooks/useModel";
import { fileNameWithoutExtension } from "../../utils/fileUtils";

const help_text: JSX.Element = (
  <div>
    <h5>Prepare your AWS DeepRacer model</h5>
    <ul>
      <li>
        Export your DeepRacer model from the AWS DeepRacer console to your local
        machine.{" "}
        <a href="https://docs.aws.amazon.com/deepracer/latest/developerguide/import-export-models.html">
          Import and export models in the AWS DeepRacer console
        </a>
      </li>
      <li>
        Ensure you have the model's reward function, training logs, metadata,
        evaluation logs, hyperparameters, and action space.
      </li>
    </ul>
    <h5>Create a zip file</h5>
    <ul>
      <li>compress the downloaded model files into a zip file</li>
      <li>
        The name of the uploaded zip file will be considered as the name of the
        model
      </li>
    </ul>
    <h5>Upload your model</h5>
    <ul>
      <li>Click "upload model" and select t</li>
      <li>Upload your exported DeepRacer model files as a zip file.</li>
      <li>
        The model will be processed into format suitable for analysis by an LLM
      </li>
    </ul>
  </div>
);

function Page() {
  const [selectedItems, setSelectedItems] = useState<any[]>([]);
  const [disabledItems, setDisabledItems] = useState<string[]>([]);

  const { addHelp } = useLayoutContext();
  const [hasLoaded, setHasLoaded] = useState(false);
  useEffect(() => {
    if (hasLoaded) {
      addHelp(help_text);
    } else {
      setHasLoaded(true);
    }
  }, [hasLoaded]);

  const { models, isLoading, error, addModel, deleteModelsHandler } =
    useModels();

  const onUploadSuccessfulHandler = useCallback((fileName: string) => {
    const fileNameWithoutExt = fileNameWithoutExtension(fileName);

    addModel({
      modelName: fileNameWithoutExt,
      status: ModelStatus.uploaded,
      __typename: "Model",
    });
    setDisabledItems((prevDisabledItems) => [
      ...prevDisabledItems,
      fileNameWithoutExt,
    ]);
  }, []);

  const deleteModels = useCallback(async () => {
    const modelNamesToDelete = selectedItems.map((item) => item.modelName);
    deleteModelsHandler(modelNamesToDelete);
    setSelectedItems([]);
  }, [selectedItems]);

  const columnDefinitions = useMemo(
    () => [
      {
        id: "modelName",
        header: "Model Name",
        cell: (item: any) => item.modelName,
        sortingField: "modelName",
        isRowHeader: true,
      },
      {
        id: "status",
        header: "Status",
        cell: (item: any) => {
          if (item.status === "uploaded") {
            return "Parsing...";
          }
          return item.status;
        },
        sortingField: "status",
        isRowHeader: true,
      },

      {
        id: "statusDetails",
        header: "Status Details",
        cell: (item: any) => item.statusDetails,
        sortingField: "statusDetails",
        isRowHeader: true,
      },
    ],
    []
  );

  return (
    <ContentLayout>
      <Table
        renderAriaLive={({ firstIndex, lastIndex, totalItemsCount }) =>
          `Displaying items ${firstIndex} to ${lastIndex} of ${totalItemsCount}`
        }
        onSelectionChange={({ detail }) =>
          setSelectedItems(detail.selectedItems)
        }
        selectedItems={selectedItems}
        ariaLabels={{
          selectionGroupLabel: "Items selection",
          allItemsSelectionLabel: ({ selectedItems }) =>
            `${selectedItems.length} ${
              selectedItems.length === 1 ? "item" : "items"
            } selected`,
          itemSelectionLabel: ({ selectedItems }, item) => item.name,
        }}
        columnDefinitions={columnDefinitions}
        columnDisplay={[
          { id: "modelName", visible: true },
          { id: "status", visible: true },
          { id: "statusDetails", visible: true },
        ]}
        enableKeyboardNavigation
        items={models}
        loadingText="Loading Models"
        loading={isLoading}
        selectionType="multi"
        trackBy="modelName"
        variant="full-page"
        isItemDisabled={(item) => item.status === "uploaded"}
        empty={
          <Box margin={{ vertical: "xs" }} textAlign="center" color="inherit">
            <SpaceBetween size="m">
              <b>No Models Found</b>
              <ModelUploadButton
                onUploadSuccessful={onUploadSuccessfulHandler}
              />
            </SpaceBetween>
          </Box>
        }
        filter={
          <TextFilter filteringPlaceholder="Find resources" filteringText="" />
        }
        header={
          <Header
            counter={`(${
              selectedItems.length ? selectedItems.length + "/" : ""
            }${models.length})`}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  onClick={deleteModels}
                  disabled={selectedItems.length === 0}
                >
                  Delete models
                </Button>
                <ModelUploadButton
                  onUploadSuccessful={onUploadSuccessfulHandler}
                />
              </SpaceBetween>
            }
          >
            Manage Models
          </Header>
        }
      />
    </ContentLayout>
  );
}

export default withAuth(Page);
