import { useState } from 'react';

const save = (key: string, value: string) => localStorage.setItem(key, JSON.stringify(value));

const load = (key: string) => {
  const value = localStorage.getItem(key);
  try {
    return value && JSON.parse(value);
  } catch (e) {
    console.warn(
      `⚠️ The ${key} value that is stored in localStorage is incorrect. Try to remove the value ${key} from localStorage and reload the page`
    );
    return undefined;
  }
};

export const useLocalStorage = (key: string, defaultValue: object) => {
  const [value, setValue] = useState(() => load(key) ?? defaultValue);

  function handleValueChange(newValue: string) {
    setValue(newValue);
    save(key, newValue);
  }

  return [value, handleValueChange];
};