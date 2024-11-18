import { useAuthenticator } from "@aws-amplify/ui-react";
import { generateClient } from "aws-amplify/api";
import { useCallback, useEffect, useMemo, useState } from "react";
import { GetModelsQuery } from "../API";
import { deleteModels } from "../graphql/mutations";
import { getModels } from "../graphql/queries";
import { onModelAdded, onModelsDeleted } from "../graphql/subscriptions";

/**
 * Represents a model fetched from the API.
 */
export type Model = NonNullable<GetModelsQuery["getModels"]>[number];

/**
 * Custom hook for fetching and deleting models.
 * @param userId - The user ID associated with the models.
 * @returns An object containing the models and loading state.
 */
export const useModels = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [
    onModelAddedSubscriptionConnected,
    setOnModelAddedSubscriptionConnected,
  ] = useState(false);
  const [
    sonModelDeletedSubscriptionConnected,
    setOnModelDeletedSubscriptionConnected,
  ] = useState(false);

  const client = useMemo(() => generateClient(), []);
  const { user } = useAuthenticator((context) => [context.authStatus]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        console.info("Fetching models");
        const response = (await client.graphql({
          query: getModels,
        })) as { data: GetModelsQuery; errors: any[] };
        const fetchedModels = response.data.getModels;
        setModels(fetchedModels!);
      } catch (err) {
        setError(
          err instanceof Error
            ? err
            : new Error("An error occurred while fetching models")
        );
      } finally {
        setIsLoading(false);
      }
    };
    fetchModels();
  }, []);

  const setupOnModelAddedSubscription = useCallback(async () => {
    console.info("Setting up onModelAdded subscription...");
    const userId = user?.userId;
    const subscription = await client.graphql({
      query: onModelAdded,
      variables: { userId },
    });

    if ("subscribe" in subscription) {
      setOnModelAddedSubscriptionConnected(true);
      const onModelAddedSubscription = subscription.subscribe({
        next: ({ data }: any) => {
          const newModels = data.onModelAdded.models;
          console.info("New models added:", newModels);
          setModels((prevItems: Model[]) => {
            console.info("Old items:", prevItems);

            const updatedItems: Model[] = prevItems.map((item) => {
              const matchingNewModel = newModels.find(
                (newModel: Model) => item?.modelName === newModel?.modelName
              );

              if (matchingNewModel) {
                // Update the existing model with the matching new model
                console.info("Updating existing model:", item?.modelName);
                return matchingNewModel;
              }
              console.info("Adding new model", item?.modelName);
              return item;
            });

            // Check if any new models are not present in the updated items
            const newModelsToAdd: Model[] = newModels.filter(
              (newModel: Model) =>
                !updatedItems.some(
                  (item) => item!.modelName === newModel!.modelName
                )
            );

            // Add the new models that are not present
            const finalItems: Model[] = [...updatedItems, ...newModelsToAdd];

            console.info("New items:", finalItems);
            return finalItems;
          });
        },
        error: (error: any) => {
          console.error(error);
          setOnModelAddedSubscriptionConnected(false);
        },
      });
      return () => {
        if ("unsubscribe" in onModelAddedSubscription) {
          onModelAddedSubscription.unsubscribe();
        }
      };
    }
  }, [client, user?.userId]);

  const setupOnModelDeletedSubscription = useCallback(async () => {
    console.info("Setting up onModelDeleted subscription...");
    const userId = user?.userId;
    const subscription = await client.graphql({
      query: onModelsDeleted,
      variables: { userId },
    });

    if ("subscribe" in subscription) {
      setOnModelDeletedSubscriptionConnected(true);
      const onModelDeletedSubscription = subscription.subscribe({
        next: ({ data }: any) => {
          const deletedModels = data.onModelsDeleted.models;
          console.info("Models deleted:", deletedModels);
          setModels((prevItems: Model[]) => {
            console.info("Old items:", prevItems);

            const updatedItems: Model[] = prevItems.filter((item) => {
              const isModelDeleted = deletedModels.some(
                (deletedModel: Model) =>
                  item?.modelName === deletedModel?.modelName
              );

              if (!isModelDeleted) {
                // Keep the item if it's not in the deletedModels array
                return true;
              }

              return false;
            });

            console.info("New items:", updatedItems);
            return updatedItems;
          });
        },
        error: (error: any) => {
          console.error(error);
          setOnModelDeletedSubscriptionConnected(false);
        },
      });
      return () => {
        if ("unsubscribe" in onModelDeletedSubscription) {
          onModelDeletedSubscription.unsubscribe();
        }
      };
    }
  }, [client, user?.userId]);

  useEffect(() => {
    setupOnModelAddedSubscription();
    setupOnModelDeletedSubscription();
  }, [setupOnModelAddedSubscription, setupOnModelDeletedSubscription]);

  const addModel = (newModel: Model) => {
    console.info("Adding model:", newModel);
    setModels((prevItems) => {
      const existingModelIndex = prevItems.findIndex(
        (item) => item?.modelName === newModel?.modelName
      );

      if (existingModelIndex !== -1) {
        // Update the existing model
        const updatedItems = [...prevItems];
        updatedItems[existingModelIndex] = newModel;
        return updatedItems;
      } else {
        // Add the new model
        return [...prevItems, newModel];
      }
    });
  };

  const deleteModelsHandler = useCallback(
    async (modelNamesToDelete: string[]) => {
      try {
        await client.graphql({
          query: deleteModels,
          variables: {
            modelNames: modelNamesToDelete,
          },
        });
      } catch (error) {
        console.error("Error deleting models:", error);
      }
    },
    [client]
  );

  return { models, isLoading, error, addModel, deleteModelsHandler };
};
