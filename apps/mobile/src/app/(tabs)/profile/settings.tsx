import { Button } from '@rozumari/ui/components/button'
import { Typography } from '@rozumari/ui/components/typography'
import * as Constants from 'expo-constants'
import { useRouter } from 'expo-router'
import { View } from 'react-native'

import { ProfileSettingsTheme } from '@/components/profile/settings/theme'

export default function TabsProfileSettingsScreen() {
  const router = useRouter()

  return (
    <View className='gap-4 p-4'>
      <ProfileSettingsTheme />

      <View className='gap-2'>
        <Typography variant='h3'>Device Configuration</Typography>
        <Button onPress={() => router.push('/(tabs)/profile/config')}>
          Configure
        </Button>
      </View>

      <View className='gap-2'>
        <Typography variant='h3'>App Build Number</Typography>
        <Typography>
          {Constants.default.expoConfig?.android?.versionCode ||
            Constants.default.expoConfig?.ios?.buildNumber ||
            Constants.default.expoConfig?.extra?.buildNumber ||
            'N/A'}
        </Typography>
      </View>

      <View className='gap-2'>
        <Typography variant='h3'>App Version</Typography>
        <Typography>{Constants.default.expoConfig?.version}</Typography>
      </View>
    </View>
  )
}
