import { ResetPasswordDto } from '@rozumari/contract/auth/dto/reset-password.dto'
import { Button } from '@rozumari/ui/components/button'
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
  FieldSet,
} from '@rozumari/ui/components/field'
import { Input } from '@rozumari/ui/components/input'
import { toast } from '@rozumari/ui/components/toast'
import { FormBuilder } from '@rozumari/ui/lib/form-builder'
import { Link, useNavigate } from 'react-router'

import { api } from '@/lib/runtime'

const forgotPasswordForm = FormBuilder.empty
  .add('password', ResetPasswordDto.Input.fields.password)
  .add('confirmPassword', ResetPasswordDto.Input.fields.password)
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    issue: 'Passwords do not match',
  })
  .make()

export function ResetPasswordForm({ token }: { token: string }) {
  const navigate = useNavigate()

  return (
    <forgotPasswordForm.Root
      defaultValues={{ password: '', confirmPassword: '' }}
      render={({ handleSubmit }) => (
        <form
          className='px-4'
          onSubmit={(e) => {
            e.preventDefault()

            handleSubmit(
              (payload) =>
                api.auth['reset-password'].mutateEffect({
                  headers: { Authorization: `Bearer ${token}` },
                  payload,
                }),
              {
                onSuccess: () => {
                  navigate('/login', { replace: true })
                  toast.add({
                    type: 'success',
                    description: 'Password reset successfully.',
                  })
                },
              }
            )
          }}
        />
      )}
    >
      <FieldSet className='group-data-[pending=true]/form:pointer-events-none'>
        <legend className='sr-only'>Forgot Password</legend>

        <forgotPasswordForm.Field
          name='password'
          render={({ field, meta }) => (
            <Field data-invalid={meta.errors.length > 0}>
              <FieldLabel htmlFor={field.id}>Password</FieldLabel>
              <Input
                {...field}
                type='password'
                disabled={meta.isPending}
                onChange={(e) => field.onChange(e.target.value)}
              />
              <FieldError id={meta.errorId} errors={meta.errors} />
            </Field>
          )}
        />

        <forgotPasswordForm.Field
          name='confirmPassword'
          render={({ field, meta }) => (
            <Field data-invalid={meta.errors.length > 0}>
              <FieldLabel htmlFor={field.id}>Confirm Password</FieldLabel>
              <Input
                {...field}
                type='password'
                disabled={meta.isPending}
                onChange={(e) => field.onChange(e.target.value)}
              />
              <FieldError id={meta.errorId} errors={meta.errors} />
            </Field>
          )}
        />

        <Field>
          <forgotPasswordForm.Submit
            render={({ meta }) => (
              <Button
                type='submit'
                form={meta.formId}
                disabled={meta.isPending}
              >
                {meta.isPending ? 'Sending...' : 'Send Reset Link'}
              </Button>
            )}
          />

          <FieldDescription>
            Remembered your password? <Link to='/login'>Login</Link>
          </FieldDescription>
        </Field>
      </FieldSet>
    </forgotPasswordForm.Root>
  )
}
