import { RegisterDto } from '@rozumari/contract/auth/dto/register.dto'
import { Button } from '@rozumari/ui/components/button'
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from '@rozumari/ui/components/field'
import { Input } from '@rozumari/ui/components/input'
import { toast } from '@rozumari/ui/components/toast'
import { FormBuilder } from '@rozumari/ui/lib/form-builder'
import { useRouter } from 'expo-router'
import { View } from 'react-native'

import { useRuntime } from '@/hooks/use-runtime'

const registerForm = FormBuilder.empty
  .add('username', RegisterDto.Input.fields.username)
  .add('email', RegisterDto.Input.fields.email)
  .add('password', RegisterDto.Input.fields.password)
  .add('confirmPassword', RegisterDto.Input.fields.password)
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    issue: 'Passwords do not match',
  })
  .make()

export default function RegisterScreen() {
  const router = useRouter()
  const { api } = useRuntime()

  return (
    <registerForm.Root
      defaultValues={{
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
      }}
      render={() => (
        <FieldSet containerClassName='p-4' className='justify-center' />
      )}
    >
      <FieldLegend>Register</FieldLegend>
      <FieldDescription>
        Fill in the form below to create a new account. You can also register
        using your social media accounts.
      </FieldDescription>

      <FieldGroup>
        <registerForm.Field
          name='username'
          render={({ field: { onChange, ...field }, meta }) => (
            <Field>
              <FieldLabel>Username</FieldLabel>
              <Input
                {...field}
                onChangeText={onChange}
                placeholder='Enter your username'
                editable={!meta.isPending}
              />
              <FieldError errors={meta.errors} />
            </Field>
          )}
        />

        <registerForm.Field
          name='email'
          render={({ field: { onChange, ...field }, meta }) => (
            <Field>
              <FieldLabel>Email</FieldLabel>
              <Input
                {...field}
                onChangeText={onChange}
                placeholder='Enter your email'
                keyboardType='email-address'
                editable={!meta.isPending}
              />
              <FieldError errors={meta.errors} />
            </Field>
          )}
        />

        <registerForm.Field
          name='password'
          render={({ field: { onChange, ...field }, meta }) => (
            <Field>
              <FieldLabel>Password</FieldLabel>
              <Input
                {...field}
                onChangeText={onChange}
                placeholder='Enter your password'
                editable={!meta.isPending}
                secureTextEntry
              />
              <FieldError errors={meta.errors} />
            </Field>
          )}
        />

        <registerForm.Field
          name='confirmPassword'
          render={({ field: { onChange, ...field }, meta }) => (
            <Field>
              <FieldLabel>Confirm Password</FieldLabel>
              <Input
                {...field}
                onChangeText={onChange}
                placeholder='Enter your password again'
                editable={!meta.isPending}
                secureTextEntry
              />
              <FieldError errors={meta.errors} />
            </Field>
          )}
        />

        <registerForm.Submit
          render={({ handleSubmit, meta }) => (
            <Field>
              <Button
                disabled={meta.isPending}
                onPress={() =>
                  handleSubmit(
                    (payload) => api.auth.register.mutateEffect({ payload }),
                    {
                      onSuccess: () => {
                        toast.success('Registration successful')
                        router.navigate('/(auth)/login')
                      },
                      onError: (error) =>
                        toast.error('Registration failed', error.message),
                    }
                  )
                }
              >
                {meta.isPending ? 'Registering...' : 'Register'}
              </Button>
            </Field>
          )}
        />

        <View className='flex flex-row items-center'>
          <FieldDescription>Already have an account? </FieldDescription>
          <Button
            variant='link'
            onPress={() => router.navigate('/(auth)/login')}
          >
            Login here
          </Button>
        </View>
      </FieldGroup>
    </registerForm.Root>
  )
}
