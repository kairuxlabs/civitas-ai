import { useLanguage } from './LanguageContext'
import { en, type TranslationKey } from './en'
import { vi } from './vi'

const DICTIONARIES = { en, vi }

export function useTranslation() {
  const { language } = useLanguage()

  function t(key: TranslationKey): string {
    return DICTIONARIES[language][key] ?? key
  }

  return { t }
}
