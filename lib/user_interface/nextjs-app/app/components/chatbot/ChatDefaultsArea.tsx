import {
  CopyToClipboard,
  Grid,
  SpaceBetween,
} from "@cloudscape-design/components";
import React, { useMemo, useReducer } from "react";
import {
  ChatActionType,
  chatReducer,
  initialChatState,
} from "../../reducers/chatReducer";
import styles from "./ChatDefaultsArea.module.css";

const PromptBox: React.FC<{ item: String }> = React.memo(({ item }) => {
  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);

  function prompt_change(item: String) {
    dispatch({
      type: ChatActionType.SET_MESSAGE_TO_SEND,
      payload: item.toString(),
    });
  }
  return (
    <div>
      <div onClick={() => prompt_change(item)}>
        <CopyToClipboard
          copyButtonText="Copy"
          copyErrorText="Failed to copy prompt"
          copySuccessText="Prompt copied"
          textToCopy={item.toString()}
          variant="icon"
        />
        {item}
      </div>
    </div>
  );
});

const ChatDefaultsArea: React.FC<{
  prompts: string[];
  display: boolean;
}> = ({ prompts, display }) => {
  const mappedPrompts = useMemo(
    () => prompts.map((item) => <PromptBox key={item} item={item} />),
    [prompts]
  );

  return (
    <SpaceBetween size="l" direction="vertical">
      {display && (
        <div>
          <p className={styles.example_prompts}>Example prompts</p>
          <Grid
            gridDefinition={[{ colspan: 4 }, { colspan: 4 }, { colspan: 4 }]}
          >
            {mappedPrompts}
          </Grid>
        </div>
      )}
    </SpaceBetween>
  );
};

export default React.memo(ChatDefaultsArea);
