import { useCallback, useMemo, useState } from "react";

interface PasswordFormState {
  readonly currentPassword: string;
  readonly newPassword: string;
  readonly newPasswordConfirm: string;
}

interface UsePasswordFormReturn {
  readonly currentPassword: string;
  readonly newPassword: string;
  readonly newPasswordConfirm: string;
  readonly setCurrentPassword: (value: string) => void;
  readonly setNewPassword: (value: string) => void;
  readonly setNewPasswordConfirm: (value: string) => void;
  readonly isFormValid: boolean;
  readonly newPasswordErrorMessage: string;
  readonly clearFields: () => void;
}

const INITIAL_STATE: Readonly<PasswordFormState> = {
  currentPassword: "",
  newPassword: "",
  newPasswordConfirm: "",
} as const;

const usePasswordForm = (): UsePasswordFormReturn => {
  const [formState, setFormState] = useState<PasswordFormState>(INITIAL_STATE);

  const updateField = useCallback(
    (field: keyof PasswordFormState) =>
      (value: string): void => {
        setFormState((prev) => ({
          ...prev,
          [field]: value,
        }));
      },
    []
  );

  const isFormValid = useMemo((): boolean => {
    const { currentPassword, newPassword, newPasswordConfirm } = formState;
    return Boolean(
      currentPassword && newPassword && newPassword === newPasswordConfirm
    );
  }, [formState]);

  const newPasswordErrorMessage = useMemo((): string => {
    const { newPassword, newPasswordConfirm } = formState;
    return newPassword &&
      newPasswordConfirm &&
      newPassword !== newPasswordConfirm
      ? "Passwords do not match"
      : "";
  }, [formState]);

  const clearFields = useCallback((): void => {
    setFormState(INITIAL_STATE);
  }, []);

  return {
    ...formState,
    setCurrentPassword: updateField("currentPassword"),
    setNewPassword: updateField("newPassword"),
    setNewPasswordConfirm: updateField("newPasswordConfirm"),
    isFormValid,
    newPasswordErrorMessage,
    clearFields,
  };
};

export default usePasswordForm;
