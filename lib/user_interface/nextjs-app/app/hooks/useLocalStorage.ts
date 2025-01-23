import { useState } from "react";

/**
 * Represents the types of values that can be stored in localStorage.
 * Extends this type if additional storage types are needed.
 */
type StorageValue = string | object | number | boolean;

/**
 * Configuration options for localStorage operations.
 * @interface StorageOptions
 * @property {Function} serializer - Function to convert value to string before storage
 * @property {Function} deserializer - Function to convert stored string back to original type
 */
interface StorageOptions {
  serializer?: (value: StorageValue) => string;
  deserializer?: (value: string) => StorageValue;
}

/**
 * Default serialization options using JSON methods.
 * Override these if custom serialization is needed.
 */
const defaultOptions: StorageOptions = {
  serializer: JSON.stringify,
  deserializer: JSON.parse,
};

/**
 * Saves a value to localStorage with error handling.
 * @param {string} key - The key under which to store the value
 * @param {StorageValue} value - The value to store
 * @param {StorageOptions} options - Serialization options
 */
const saveToStorage = (
  key: string,
  value: StorageValue,
  options: StorageOptions = defaultOptions
): void => {
  try {
    const serializedValue = options.serializer!(value);
    localStorage.setItem(key, serializedValue);
  } catch (error) {
    console.error(`Error saving to localStorage: ${error}`);
  }
};

/**
 * Loads a value from localStorage with error handling.
 * @param {string} key - The key to retrieve
 * @param {StorageOptions} options - Deserialization options
 * @returns {StorageValue | undefined} The stored value or undefined if not found/error
 */
const loadFromStorage = (
  key: string,
  options: StorageOptions = defaultOptions
): StorageValue | undefined => {
  try {
    const item = localStorage.getItem(key);
    return item ? options.deserializer!(item) : undefined;
  } catch (error) {
    // Sanitize the key before logging
    const sanitizedKey = String(key).replace(/[\r\n%]/g, '');
    
    // Log with sanitized input and minimal error information
    console.warn(
      "⚠️ Error reading from localStorage.",
      { key: sanitizedKey },
      error instanceof Error ? error.message : 'Unknown error'
    );
    return undefined;
  }
};

/**
 * A custom React hook that provides persistent storage using localStorage with
 * automatic serialization/deserialization and error handling.
 *
 * @template T - The type of value being stored (must extend StorageValue)
 * @param {string} key - The key under which to store the value in localStorage
 * @param {T} defaultValue - The default value to use if no value is stored
 * @param {StorageOptions} options - Custom serialization/deserialization options
 * @returns {[T, (newValue: T) => void]} A tuple containing the stored value and a setter function
 *
 * @example
 * // Basic usage
 * const [value, setValue] = useLocalStorage('myKey', 'default value');
 *
 * @example
 * // With custom serialization
 * const [value, setValue] = useLocalStorage('myKey', { date: new Date() }, {
 *   serializer: (v) => JSON.stringify({ ...v, date: v.date.toISOString() }),
 *   deserializer: (s) => {
 *     const parsed = JSON.parse(s);
 *     return { ...parsed, date: new Date(parsed.date) };
 *   },
 * });
 */
export const useLocalStorage = <T extends StorageValue>(
  key: string,
  defaultValue: T,
  options: StorageOptions = defaultOptions
): [T, (newValue: T) => void] => {
  // Initialize state with stored value or default
  const [storedValue, setStoredValue] = useState<T>(() => {
    const value = loadFromStorage(key, options);
    return (value ?? defaultValue) as T;
  });

  /**
   * Updates both the React state and localStorage value.
   * Supports both direct values and functional updates.
   * @param {T | ((prevValue: T) => T)} newValue - New value or update function
   */
  const setValue = (newValue: T): void => {
    try {
      // Handle function updates similar to useState
      const valueToStore =
        newValue instanceof Function ? newValue(storedValue) : newValue;

      // Update React state
      setStoredValue(valueToStore);

      // Update localStorage
      saveToStorage(key, valueToStore, options);
    } catch (error) {
      console.error(`Error setting value in useLocalStorage: ${error}`);
    }
  };

  return [storedValue, setValue];
};
