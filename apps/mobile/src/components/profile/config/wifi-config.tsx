import { Button } from '@rozumari/ui/components/button'
import { Input } from '@rozumari/ui/components/input'
import { toast } from '@rozumari/ui/components/toast'
import { Typography } from '@rozumari/ui/components/typography'
import React, { useEffect, useState } from 'react'
import { View } from 'react-native'

import {
  ACTION_CODES,
  STATUS_CODES,
  useBLE,
} from '@/components/profile/config/_context'

export function WifiConfig() {
  const { isConnected, sendBleCommand, registerByteHandler } = useBLE()
  const [ssid, setSsid] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [isCheckingWifi, setIsCheckingWifi] = useState<boolean>(false)
  const [isWifiValid, setIsWifiValid] = useState<boolean>(false)

  useEffect(
    () =>
      registerByteHandler((action, status) => {
        if (action === ACTION_CODES.CHECK_WIFI_RES) {
          setIsCheckingWifi(false)
          if (status === STATUS_CODES.SUCCESS) {
            setIsWifiValid(true)
            toast.success('Wi-Fi credentials are valid!')
          } else {
            setIsWifiValid(false)
            toast.error('Wi-Fi credentials are invalid!')
          }
        } else if (action === ACTION_CODES.SET_WIFI_RES) {
          if (status === STATUS_CODES.SUCCESS) {
            toast.success('Saved Wi-Fi to device!')
          } else {
            toast.error('Failed to save Wi-Fi!')
          }
        }
      }),
    [registerByteHandler]
  )

  if (!isConnected) return null

  const handleCheckWifi = async () => {
    if (!ssid || !password) return
    setIsCheckingWifi(true)
    setIsWifiValid(false)
    await sendBleCommand('check_wifi', { ssid, password })
  }

  const handleSaveWifi = async () => {
    if (!ssid || !password) return
    await sendBleCommand('set_wifi', { ssid, password })
  }

  const getCheckWifiLabel = () => {
    if (isCheckingWifi) return 'Testing Connection...'
    if (isWifiValid) return 'Wi-Fi Valid ✓'
    return 'Check Wi-Fi'
  }

  return (
    <View className='gap-3'>
      <Typography className='font-semibold'>Wi-Fi Configuration</Typography>

      <Input
        placeholder='Wi-Fi SSID'
        value={ssid}
        onChangeText={(text) => {
          setSsid(text)
          setIsWifiValid(false)
        }}
      />

      <Input
        placeholder='Wi-Fi Password'
        secureTextEntry
        value={password}
        onChangeText={(text) => {
          setPassword(text)
          setIsWifiValid(false)
        }}
      />

      <Button
        variant={isWifiValid ? 'success' : 'secondary'}
        onPress={handleCheckWifi}
        disabled={!ssid || !password || isCheckingWifi}
      >
        {getCheckWifiLabel()}
      </Button>

      <Button
        onPress={handleSaveWifi}
        disabled={!isWifiValid || isCheckingWifi}
      >
        Save Wi-Fi
      </Button>
    </View>
  )
}
