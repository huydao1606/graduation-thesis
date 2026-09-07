import {
  CardDescription,
  CardHeader,
  CardTitle,
} from '@rozumari/ui/components/card'
import { useSearchParams } from 'react-router'

import { ResetPasswordForm } from '@/routes/auth/_components/reset-password-form'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()

  const token = searchParams.get('token')

  if (!token)
    return (
      <CardHeader>
        <CardTitle>Invalid Token</CardTitle>
      </CardHeader>
    )

  return (
    <>
      <CardHeader>
        <CardTitle>Forgot Password</CardTitle>
        <CardDescription>
          Enter your email address and we&apos;ll send you a link to reset your
          password.
        </CardDescription>
      </CardHeader>

      <ResetPasswordForm token={token} />
    </>
  )
}
