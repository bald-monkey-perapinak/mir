declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp
    }
  }
}

interface TelegramWebApp {
  initData: string
  initDataUnsafe: {
    user?: {
      id: number
      first_name: string
      last_name?: string
      username?: string
    }
  }
  ready: () => void
  expand: () => void
  close: () => void
  MainButton: {
    text: string
    show: () => void
    hide: () => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
    showProgress: (leaveActive?: boolean) => void
    hideProgress: () => void
    isVisible: boolean
  }
  BackButton: {
    show: () => void
    hide: () => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
  }
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
  }
  colorScheme: 'light' | 'dark'
  themeParams: Record<string, string>
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
}

export const tg = window.Telegram?.WebApp

export function getTelegramInitData(): string {
  return tg?.initData || ''
}

export function setupTelegram() {
  if (tg) {
    tg.ready()
    tg.expand()
    document.body.classList.add('tg-mode')
  }
}

export function hapticSuccess() {
  tg?.HapticFeedback?.notificationOccurred('success')
}

export function hapticError() {
  tg?.HapticFeedback?.notificationOccurred('error')
}

export function hapticLight() {
  tg?.HapticFeedback?.impactOccurred('light')
}

export function showBackButton(onClick: () => void) {
  if (!tg) return
  tg.BackButton.show()
  tg.BackButton.onClick(onClick)
  return () => {
    tg.BackButton.offClick(onClick)
    tg.BackButton.hide()
  }
}
