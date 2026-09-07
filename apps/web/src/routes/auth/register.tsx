import {
  CardHeader,
  CardTitle,
  CardDescription,
} from '@rozumari/ui/components/card'

import { createMetadata } from '@/lib/metadata'
import { RegisterForm } from '@/routes/auth/_components/register-form'

export const meta = () =>
  createMetadata({
    title: 'Register',
    description: 'Create an account to access all features.',
  })

export default function RegisterPage() {
  return (
    <>
      <CardHeader>
        <CardTitle>Register</CardTitle>
        <CardDescription>
          Create an account to access all features.
        </CardDescription>
      </CardHeader>

      <RegisterForm />
    </>
  )
}
