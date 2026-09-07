import { Typography } from '@rozumari/ui/components/typography'

import { createMetadata } from '@/lib/metadata'
import { ChangePasswordForm } from '@/routes/dashboard/account/_components/change-password-form'

export const meta = () =>
  createMetadata({
    title: 'Change Password',
    description: 'Update your password to keep your account secure.',
  })

export default function ChangePasswordPage() {
  return (
    <>
      <Typography variant='h2'>Change Password</Typography>
      <Typography>
        Update your password to keep your account secure. If you signed in with
        a social account, leave the current password blank to set one.
      </Typography>

      <ChangePasswordForm />
    </>
  )
}
