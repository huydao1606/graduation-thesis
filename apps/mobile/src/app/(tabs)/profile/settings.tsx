import { Button } from '@rozumari/ui/components/button'
import { RadioGroup, RadioGroupItem } from '@rozumari/ui/components/radio-group'
import { Typography } from '@rozumari/ui/components/typography'
import * as Constants from 'expo-constants'
import { useRouter } from 'expo-router'
import { View } from 'react-native'
import { Uniwind, useUniwind } from 'uniwind'

import { setTheme } from '@/lib/secure-store'

export default function TabsProfileSettingsScreen() {
  const { theme, hasAdaptiveThemes } = useUniwind()
  const router = useRouter()

  return (
    <View className='gap-4 p-4'>
      <View className='gap-2'>
        <Typography variant='h3'>Dark Mode</Typography>

        <RadioGroup
          value={hasAdaptiveThemes ? 'system' : theme}
          onValueChange={async (value) => {
            await setTheme(value as 'light' | 'dark' | 'system')
            Uniwind.setTheme(value as 'light' | 'dark' | 'system')
          }}
        >
          <RadioGroupItem value='light'>
            <Typography>Off</Typography>
          </RadioGroupItem>
          <RadioGroupItem value='dark'>
            <Typography>On</Typography>
          </RadioGroupItem>
          <RadioGroupItem value='system'>
            <Typography>Use device settings</Typography>
          </RadioGroupItem>
        </RadioGroup>
      </View>

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
