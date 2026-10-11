import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, Eye, EyeOff, Loader2, User, Mail, Lock } from 'lucide-react';
import AuthLayout from './AuthLayout';
import AuthField from './AuthField';

export default function Signup() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { signup } = useAuth();
  const navigate = useNavigate();
  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email);
  const isPasswordValid = formData.password.length >= 6;
  const canSubmit = Boolean(
    formData.name.trim() &&
    isEmailValid &&
    isPasswordValid &&
    !isLoading
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error on input change for better UX
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Optional: basic client-side validation
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setIsLoading(false);
      return;
    }

    try {
      await signup(
        formData.name.trim(),
        formData.email.trim(),
        formData.password
      );
      navigate('/dashboard', { replace: true });
    } catch (err) {
      let message = 'Failed to create account. Please try again.';

      // Common Firebase Auth errors
      if (err.code === 'auth/email-already-in-use') {
        message = 'This email is already registered.';
      } else if (err.code === 'auth/invalid-email') {
        message = 'Please enter a valid email address.';
      } else if (err.code === 'auth/weak-password') {
        message = 'Password is too weak. Use at least 6 characters.';
      } else if (err.code === 'auth/operation-not-allowed') {
        message = 'Account creation is currently disabled.';
      }

      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
  <AuthLayout
    title="Create your workspace"
    subtitle="Start asking questions across your documents."
  >
    {error && (
      <div role="alert" className="mb-5 flex gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{error}</span>
      </div>
    )}

    <form onSubmit={handleSubmit} className="space-y-5">
      <AuthField
        id="name"
        label="Full name"
        icon={User}
        name="name"
        type="text"
        autoComplete="name"
        required
        value={formData.name}
        onChange={handleChange}
        placeholder="Ujjwal Sinha"
      />

      <AuthField
        id="email"
        label="Email"
        icon={Mail}
        name="email"
        type="email"
        autoComplete="email"
        required
        value={formData.email}
        onChange={handleChange}
        placeholder="you@example.com"
      />

      <AuthField
        id="password"
        label="Password"
        icon={Lock}
        name="password"
        type={showPassword ? 'text' : 'password'}
        autoComplete="new-password"
        required
        value={formData.password}
        onChange={handleChange}
        placeholder="Minimum 6 characters"
        rightElement={
          <button
            type="button"
            onClick={() => setShowPassword((value) => !value)}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        }
      />

      <p className="text-xs text-gray-500 dark:text-gray-400">
        Use at least 6 characters.
      </p>

      <button
        type="submit"
        disabled={!canSubmit}
        className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Creating account...
          </>
        ) : (
          "Create account"
        )}
      </button>
    </form>

    <div className="mt-6 text-center text-sm">
      <span className="text-gray-600 dark:text-gray-400">Already have an account? </span>
      <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
        Sign in
      </Link>
    </div>
  </AuthLayout>
);
}
