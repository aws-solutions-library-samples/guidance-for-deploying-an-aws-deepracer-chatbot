import { ImageContentInput } from "../API";

interface ChatState {
  messageToSend: string;
  sendButtonDisabled: boolean;
  noRowsMessageBox: number;
  thumbnails?: string[];
  imageInputs?: ImageContentInput[];
}

// Define the action types
type ChatAction =
  | { type: "SET_MESSAGE_TO_SEND"; payload: string }
  | { type: "SET_SEND_BUTTON_DISABLED"; payload: boolean }
  | { type: "INCREMENT_ROWS" }
  | { type: "RESET_MESSAGE_STATE" }
  | { type: "RESET_ALL" }
  | {
      type: "SET_THUMBNAILS_AND_INPUTS";
      payload: { thumbnails: string[]; imageInputs: ImageContentInput[] };
    };

export const initialChatState: ChatState = {
  messageToSend: "",
  sendButtonDisabled: false,
  noRowsMessageBox: 1,
};

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "SET_MESSAGE_TO_SEND":
      return { ...state, messageToSend: action.payload };
    case "SET_SEND_BUTTON_DISABLED":
      return { ...state, sendButtonDisabled: action.payload };
    case "INCREMENT_ROWS":
      return { ...state, noRowsMessageBox: state.noRowsMessageBox + 1 };
    case "RESET_MESSAGE_STATE":
      return { ...state, messageToSend: "", noRowsMessageBox: 1 };
    case "RESET_ALL":
      return initialChatState;
    case "SET_THUMBNAILS_AND_INPUTS":
      return { ...state, ...action.payload };
    default:
      return state;
  }
}
