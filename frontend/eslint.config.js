import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // React 19 新规则，对"Dialog reset on open" / "controlled input draft sync"
      // 等合法 UX 场景过严；项目确实需要在 effect 内 setState。
      // 未来切换到 React 19 Compiler 可重启此规则并重构 pattern。
      'react-hooks/set-state-in-effect': 'off',
    },
  },
])
