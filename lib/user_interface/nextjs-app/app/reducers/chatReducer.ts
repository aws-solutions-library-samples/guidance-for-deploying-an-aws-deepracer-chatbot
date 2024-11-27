/**
 * @fileoverview Chat state management using Redux pattern
 */

import { ImageContentInput } from "../API";

/**
 * Initial number of rows in the message box
 * @constant {number}
 */
const INITIAL_ROW_COUNT = 1;

/**
 * Enumeration of all possible chat action types
 * @enum {string}
 */
export enum ChatActionType {
  /** Update the message being composed */
  SET_MESSAGE_TO_SEND = "SET_MESSAGE_TO_SEND",
  /** Enable/disable the send button */
  SET_SEND_BUTTON_DISABLED = "SET_SEND_BUTTON_DISABLED",
  /** Increase the number of rows in message box */
  INCREMENT_ROWS = "INCREMENT_ROWS",
  /** Reset message-related state */
  RESET_MESSAGE_STATE = "RESET_MESSAGE_STATE",
  /** Reset entire chat state */
  RESET_ALL = "RESET_ALL",
  /** Update image thumbnails and inputs */
  SET_THUMBNAILS_AND_INPUTS = "SET_THUMBNAILS_AND_INPUTS",
}

/**
 * Interface defining the shape of the chat state
 * @interface ChatState
 */
interface ChatState {
  /** Current message being composed */
  messageToSend: string;
  /** Whether the send button is disabled */
  sendButtonDisabled: boolean;
  /** Number of rows in the message box */
  noRowsMessageBox: number;
  /** Array of thumbnail URLs */
  thumbnails?: string[];
  /** Array of image content inputs */
  imageInputs?: ImageContentInput[];
}

/**
 * Type defining the payload types for each action
 * @type {Object}
 */
type ChatActionPayload = {
  [ChatActionType.SET_MESSAGE_TO_SEND]: string;
  [ChatActionType.SET_SEND_BUTTON_DISABLED]: boolean;
  [ChatActionType.INCREMENT_ROWS]: undefined;
  [ChatActionType.RESET_MESSAGE_STATE]: undefined;
  [ChatActionType.RESET_ALL]: undefined;
  [ChatActionType.SET_THUMBNAILS_AND_INPUTS]: {
    thumbnails: string[];
    imageInputs: ImageContentInput[];
  };
};

/**
 * Union type of all possible chat actions
 * @type {ChatAction}
 */
type ChatAction =
  | { type: ChatActionType.SET_MESSAGE_TO_SEND; payload: string }
  | { type: ChatActionType.SET_SEND_BUTTON_DISABLED; payload: boolean }
  | { type: ChatActionType.INCREMENT_ROWS }
  | { type: ChatActionType.RESET_MESSAGE_STATE }
  | { type: ChatActionType.RESET_ALL }
  | {
      type: ChatActionType.SET_THUMBNAILS_AND_INPUTS;
      payload: { thumbnails: string[]; imageInputs: ImageContentInput[] };
    };

/**
 * Initial state for the chat reducer
 * @type {ChatState}
 */
export const initialChatState: ChatState = {
  messageToSend: "",
  sendButtonDisabled: false,
  noRowsMessageBox: INITIAL_ROW_COUNT,
};

/**
 * Action creators for chat operations
 * @namespace chatActions
 */
export const chatActions = {
  /**
   * Creates an action to update the message being composed
   * @param {string} message - The new message
   * @returns {ChatAction} Action object
   */
  setMessageToSend: (message: string): ChatAction => ({
    type: ChatActionType.SET_MESSAGE_TO_SEND,
    payload: message,
  }),

  /**
   * Creates an action to enable/disable the send button
   * @param {boolean} disabled - Whether the button should be disabled
   * @returns {ChatAction} Action object
   */
  setSendButtonDisabled: (disabled: boolean): ChatAction => ({
    type: ChatActionType.SET_SEND_BUTTON_DISABLED,
    payload: disabled,
  }),

  /**
   * Creates an action to increment the message box rows
   * @returns {ChatAction} Action object
   */
  incrementRows: (): ChatAction => ({
    type: ChatActionType.INCREMENT_ROWS,
  }),

  /**
   * Creates an action to reset message state
   * @returns {ChatAction} Action object
   */
  resetMessageState: (): ChatAction => ({
    type: ChatActionType.RESET_MESSAGE_STATE,
  }),

  /**
   * Creates an action to reset all chat state
   * @returns {ChatAction} Action object
   */
  resetAll: (): ChatAction => ({
    type: ChatActionType.RESET_ALL,
  }),

  /**
   * Creates an action to update thumbnails and image inputs
   * @param {string[]} thumbnails - Array of thumbnail URLs
   * @param {ImageContentInput[]} imageInputs - Array of image content inputs
   * @returns {ChatAction} Action object
   */
  setThumbnailsAndInputs: (
    thumbnails: string[],
    imageInputs: ImageContentInput[]
  ): ChatAction => ({
    type: ChatActionType.SET_THUMBNAILS_AND_INPUTS,
    payload: { thumbnails, imageInputs },
  }),
};

/**
 * Reducer function for chat state management
 * @param {ChatState} state - Current chat state
 * @param {ChatAction} action - Action to process
 * @returns {ChatState} New chat state
 *
 * @example
 * const [state, dispatch] = useReducer(chatReducer, initialChatState);
 * dispatch(chatActions.setMessageToSend("Hello"));
 */
export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case ChatActionType.SET_MESSAGE_TO_SEND:
      return { ...state, messageToSend: action.payload };

    case ChatActionType.SET_SEND_BUTTON_DISABLED:
      return { ...state, sendButtonDisabled: action.payload };

    case ChatActionType.INCREMENT_ROWS:
      return { ...state, noRowsMessageBox: state.noRowsMessageBox + 1 };

    case ChatActionType.RESET_MESSAGE_STATE:
    case ChatActionType.RESET_ALL:
      return initialChatState;

    case ChatActionType.SET_THUMBNAILS_AND_INPUTS:
      return {
        ...state,
        thumbnails: action.payload.thumbnails,
        imageInputs: action.payload.imageInputs,
      };

    default:
      return state;
  }
}
