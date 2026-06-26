module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  parser: "vue-eslint-parser",
  parserOptions: {
    parser: "@typescript-eslint/parser",
    ecmaVersion: "latest",
    sourceType: "module",
  },
  plugins: ["@typescript-eslint"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:vue/vue3-recommended",
  ],
  rules: {
    "vue/multi-word-component-names": "off",
    "vue/require-default-prop": "off",
    "vue/attributes-order": "off",
    "vue/singleline-html-element-content-newline": "off",
    "vue/max-attributes-per-line": "off",
    "vue/html-self-closing": "off",
    "vue/html-indent": "off",
    "vue/html-closing-bracket-newline": "off",
    "vue/first-attribute-linebreak": "off",
    "vue/no-v-html": "off",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": [
      "error",
      { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
    ],
    "no-undef": "off",
  },
  ignorePatterns: ["dist/", "node_modules/", "*.config.ts", "*.config.js"],
};
