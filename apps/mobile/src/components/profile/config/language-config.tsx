import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@rozumari/ui/components/select'
import { toast } from '@rozumari/ui/components/toast'
import { Typography } from '@rozumari/ui/components/typography'
import { useEffect } from 'react'
import { View } from 'react-native'

import {
  ACTION_CODES,
  STATUS_CODES,
  useBLE,
} from '@/components/profile/config/_context'

const LANGUAGES = [
  { label: 'English', value: 'en' },
  { label: 'Tiếng Việt', value: 'vi' },
]

export function LanguageConfig() {
  const { deviceInfo, isConnected, sendBleCommand, registerByteHandler } =
    useBLE()

  useEffect(
    () =>
      registerByteHandler((action, status) => {
        if (action === ACTION_CODES.SET_LANGUAGE_RES) {
          if (status === STATUS_CODES.SUCCESS)
            toast.success('Language updated!')
          else toast.error('Failed to update language!')
        }
      }),
    [registerByteHandler]
  )

  if (!isConnected) return null

  return (
    <View className='gap-3'>
      <Typography className='font-semibold'>Language Configuration</Typography>

      <Select
        defaultValue={deviceInfo?.language}
        onValueChange={(value) =>
          sendBleCommand('set_language', { language: value })
        }
      >
        <SelectTrigger>
          <SelectValue placeholder='Select language...' items={LANGUAGES} />
        </SelectTrigger>
        <SelectContent>
          {LANGUAGES.map((item) => (
            <SelectItem key={item.value} value={item.value}>
              {item.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </View>
  )
}
