/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  // добавьте другие переменные при необходимости
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}