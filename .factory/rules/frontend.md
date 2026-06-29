# Frontend Conventions (Vue 3 + TypeScript + TailwindCSS)

For universal code quality rules (function length, file length, nesting limits, error handling, comments), see `code-quality.md`.

## Vue Component Structure
- Use `<script setup lang="ts">` exclusively
- `defineProps<T>()` with TypeScript interface, not runtime `defineProps({})`
- `defineEmits<T>()` with typed emit signatures
- Single File Components (SFC): `<script setup>`, `<template>`, `<style>` (optional)
- Component files: `PascalCase.vue`

## Naming
- Components: `PascalCase` (file & import)
- Stores: `camelCase`, exported as `useXxxStore`
- Composables: `useXxx` prefix (e.g., `useAuth`)
- Services: `camelCase` with descriptive names
- Routes: `kebab-case` paths
- Functions/variables: `camelCase`

## TypeScript
- Strict mode enabled (`strict: true` in tsconfig)
- Path alias: `@/` maps to `src/` (e.g., `@/stores/auth`, `@/components/ui/BaseButton`)
- Type files in `src/types/`, import with `import type { Foo } from "@/types"`
- Avoid `any` -- use proper types or `unknown` with type guards
- `Record<string, string>` over `{ [key: string]: string }`

## State Management (Pinia)
- Composition API style: `defineStore("name", () => { ... })`
- `ref()` for primitive state, `computed()` for derived state
- Return everything used by components from setup function
- Async actions use `async function` inside store

## Component Organization
```
src/
├── components/
│   ├── ui/          # Reusable base components (BaseButton, BaseModal, BaseTable)
│   ├── layout/      # AppShell components (AppHeader, AppSidebar)
│   ├── dashboard/   # Dashboard-specific components
│   ├── scrape/      # Scrape workflow components
│   └── users/       # User management components
├── pages/           # Route-level page components
├── composables/     # Reusable composition functions
├── layouts/         # Layout wrapper components
├── stores/          # Pinia stores (one file per domain)
├── services/        # API client functions (axios)
├── types/           # Shared TypeScript interfaces/types
├── router/          # Vue Router configuration
└── utils/           # Pure utility functions
```

## TailwindCSS
- Utility-first -- no custom CSS unless unavoidable
- Use `class` binding with arrays/objects for conditional classes
- Responsive prefixes (`sm:`, `md:`, `lg:`) for breakpoints
- Color palette: blue-600 primary, red-600 danger, gray-* neutral

For testing conventions, see `frontend-testing.md`.
