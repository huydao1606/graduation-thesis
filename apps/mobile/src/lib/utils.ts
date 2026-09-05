import Constants from 'expo-constants'
import { Alert, Platform, ToastAndroid } from 'react-native'

/**
 * Extend this function when going to production by
 * setting the baseUrl to your production API URL.
 */
export const getBaseUrl = () => {
  /**
   * Gets the IP address of your host-machine. If it cannot automatically find it,
   * you'll have to manually set it. NOTE: Port 3000 should work for most but confirm
   * you don't have anything else running on it, or you'd have to change it.
   *
   * **NOTE**: This is only for development. In production, you'll want to set the
   * baseUrl to your production API URL.
   */
  const debuggerHost = Constants.expoConfig?.hostUri
  const localhost = debuggerHost?.split(':')[0]

  if (localhost) return `http://${localhost}:3000`

  if (process.env.EXPO_PUBLIC_API_URL) return process.env.EXPO_PUBLIC_API_URL

  throw new Error(
    'Could not determine the base URL. Please set the EXPO_PUBLIC_API_URL environment variable.'
  )
}

type ToastDuration = 'short' | 'long'
type AlertLevel = 'success' | 'error' | 'info' | 'warning'

/**
 * Show a toast notification on Android or an alert on iOS.
 * @param message The message to show in the toast or alert.
 * @param option Duration for Android ('short' | 'long') or Title level for iOS ('Error' | 'Info' | 'Warning').
 */
export function showToast(
  message: string,
  option?: ToastDuration | AlertLevel
): void {
  if (Platform.OS === 'ios') {
    const duration = option === 'long' ? ToastAndroid.LONG : ToastAndroid.SHORT
    ToastAndroid.show(message, duration)
  } else {
    const isDuration = option === 'short' || option === 'long'

    let title = isDuration || !option ? 'notification' : option
    title = title.charAt(0).toUpperCase() + title.slice(1)

    Alert.alert(title, message)
  }
}
