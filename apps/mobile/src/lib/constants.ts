import * as Constants from 'expo-constants'

export const isExpoGo =
  Constants.default.executionEnvironment ===
  Constants.ExecutionEnvironment.StoreClient
