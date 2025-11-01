import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import hooksPlugin from "eslint-plugin-react-hooks";
import refreshPlugin from "eslint-plugin-react-refresh";

export default tseslint.config(
  // The tseslint.config function flattens the array and applies configurations.
  // Start with ignores.
  {
    ignores: ["dist/", "node_modules/", "vite.config.ts", "eslint.config.js"],
  },
  // Base config for all files.
  ...tseslint.configs.recommended,
  // React specific configurations
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      react: pluginReact,
      "react-hooks": hooksPlugin,
      "react-refresh": refreshPlugin,
    },
    languageOptions: {
        globals: {
            ...globals.browser,
        },
    },
    rules: {
      ...pluginReact.configs.recommended.rules,
      ...pluginReact.configs["jsx-runtime"].rules,
      ...hooksPlugin.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
    settings: {
      react: {
        version: "detect",
      },
    },
  }
);
