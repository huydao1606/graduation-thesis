import { ActivityIndicator, View } from 'react-native'

export default function IndexScreen() {
  return (
    <View className='flex-1 items-center justify-center bg-background'>
      <ActivityIndicator size='large' colorClassName='accent-primary' />
    </View>
  )
}
