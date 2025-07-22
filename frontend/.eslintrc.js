module.exports = {
  extends: [
    'react-app',
    'react-app/jest',
    'eslint:recommended',
    'prettier'
  ],
  plugins: ['prettier'],
  rules: {
    'prettier/prettier': ['error', {
      singleQuote: true,
      trailingComma: 'es5',
      tabWidth: 2,
      semi: false,
      printWidth: 80
    }],
    'no-unused-vars': 'warn',
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'react/jsx-uses-react': 'off',
    'react/react-in-jsx-scope': 'off'
  },
  env: {
    browser: true,
    es6: true,
    jest: true
  }
}