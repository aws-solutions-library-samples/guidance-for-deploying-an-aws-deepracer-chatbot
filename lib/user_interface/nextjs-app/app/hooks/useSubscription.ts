import { generateClient } from "aws-amplify/api";
import { useCallback, useState } from "react";
import { Subscription } from "rxjs";
import { MessageResponse } from "../API";
import { onStreamResponse } from "../graphql/subscriptions";

type SubscriptionEvent = {
  data: {
    onStreamResponse: MessageResponse;
  };
};

interface UseSubscriptionResult {
  subscriptionConnected: boolean;
  setupSubscription: () => Promise<(() => void) | undefined>;
  subscriptionHandler: Subscription | undefined;
}

const useSubscription = (
  userId: string,
  sessionId: string,
  onNewMessage: (message: MessageResponse, thumbnails: string[]) => void,
  onWaitingReply?: (waiting: boolean) => void
): UseSubscriptionResult => {
  const client = generateClient();
  const [subscriptionConnected, setSubscriptionConnected] = useState(false);
  const [subscriptionHandler, setSubscriptionHandler] =
    useState<Subscription>();

  const handleSubscriptionError = (error: Error) => {
    console.error("Subscription error:", error);
    setSubscriptionConnected(false);
  };

  const setupSubscription = useCallback(async () => {
    try {
      console.info("Setting up subscription...");
      const subscription = await client.graphql({
        query: onStreamResponse,
        variables: { userId },
      });

      if ("subscribe" in subscription) {
        setSubscriptionConnected(true);

        const handler = subscription.subscribe({
          next: (event: SubscriptionEvent) => {
            onWaitingReply?.(false);
            const messageResponse = event.data.onStreamResponse;
            onNewMessage(messageResponse, []);
          },
          error: handleSubscriptionError,
        });

        setSubscriptionHandler(handler);
        return () => handler.unsubscribe();
      }
    } catch (error) {
      handleSubscriptionError(error as Error);
      return () => {};
    }
  }, [userId, onNewMessage, onWaitingReply, client]);

  return { subscriptionConnected, setupSubscription, subscriptionHandler };
};

export default useSubscription;
