import { Button } from '@rozumari/ui/components/button'
import { Typography } from '@rozumari/ui/components/typography'
import * as Linking from 'expo-linking'
import { View, ScrollView } from 'react-native'

import { useBLE, BLEProvider } from '@/components/profile/config/_context'
import { BLEConnection } from '@/components/profile/config/ble-connection'
import { LanguageConfig } from '@/components/profile/config/language-config'
import { UtcConfig } from '@/components/profile/config/utc-config'
import { WifiConfig } from '@/components/profile/config/wifi-config'

function ConfigContent() {
  const { isRequirementsMet, deviceInfo } = useBLE()

  if (!isRequirementsMet)
    return (
      <View className='flex-1 items-center justify-center gap-2 p-4'>
        <Typography variant='h3'>Bluetooth & Location Required</Typography>
        <Button onPress={() => Linking.openSettings()}>Open Settings</Button>
      </View>
    )

  const configKey = deviceInfo
    ? `${deviceInfo.utc}-${deviceInfo.language}`
    : 'default'

  return (
    <ScrollView className='p-4' contentContainerClassName='gap-4'>
      <BLEConnection />

      <LanguageConfig key={`${configKey}-lang`} />
      <UtcConfig key={`${configKey}-utc`} />

      <WifiConfig />
    </ScrollView>
  )
}

export default function ProfileConfigScreen() {
  return (
    <BLEProvider>
      <ConfigContent />
    </BLEProvider>
  )
}
