import * as Constants from 'expo-constants'

export const REFRESH_TOKEN_KEY = 'auth.refreshToken'
export const ACCESS_TOKEN_KEY = 'auth.accessToken'

export const THEME_KEY = 'config.theme'

export const isExpoGo =
  Constants.default.executionEnvironment ===
  Constants.ExecutionEnvironment.StoreClient
