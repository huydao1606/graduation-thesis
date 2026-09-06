import { Button } from '@rozumari/ui/components/button'
import { Typography } from '@rozumari/ui/components/typography'
import * as Linking from 'expo-linking'
import { useEffect, useState } from 'react'
import { Alert, View } from 'react-native'

import { isExpoGo } from '@/lib/constants'

export default function ProfileConfigScreen() {
  const [isBluetoothAvailable, setIsBluetoothAvailable] =
    useState<boolean>(false)

  useEffect(() => {
    if (isExpoGo) return

    let isMounted = true

    void (async () => {
      if (!isMounted) return

      const { default: BleManager } = await import('react-native-ble-manager')

      await BleManager.start({ showAlert: false })
      console.log('BLE Manager started')

      try {
        await BleManager.enableBluetooth()
        setIsBluetoothAvailable(true)
      } catch {
        setIsBluetoothAvailable(false)
        return Alert.alert(
          'Bluetooth is Off',
          'Please turn on Bluetooth to use this feature.'
        )
      }

      await BleManager.scan()
      console.log('Scanning for BLE devices...')

      const devices = await BleManager.getDiscoveredPeripherals()
      console.log('Discovered devices:', devices)
    })()

    return () => {
      isMounted = false
    }
  }, [])

  if (!isBluetoothAvailable)
    return (
      <View className='flex-1 items-center justify-center gap-2 p-4'>
        <Typography variant='h3'>Bluetooth is not available</Typography>
        <Typography className='text-center text-muted-foreground'>
          This feature requires Bluetooth to be enabled. Please turn on
          Bluetooth and try again.
        </Typography>
        <Button onPress={() => Linking.openSettings()}>Open Settings</Button>
      </View>
    )

  return (
    <View className='p-4'>
      <Typography variant='h1'>Profile Config</Typography>
    </View>
  )
}
