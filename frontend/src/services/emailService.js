import emailjs from '@emailjs/browser'

// Get credentials from environment variables
// Must use VITE_ prefix for frontend env vars in Vite
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY
const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID
const REGISTER_TEMPLATE_ID = import.meta.env.VITE_EMAILJS_REGISTER_TEMPLATE_ID
const FORGOT_PASSWORD_TEMPLATE_ID = import.meta.env.VITE_EMAILJS_FORGOT_PASSWORD_TEMPLATE_ID

if (!PUBLIC_KEY || !SERVICE_ID || !REGISTER_TEMPLATE_ID || !FORGOT_PASSWORD_TEMPLATE_ID) {
  console.warn('⚠️ Missing EmailJS configuration in .env file')
}

// Initialize EmailJS
emailjs.init(PUBLIC_KEY)

const emailService = {
  async sendRegistrationOTP(email, otp, userName = 'User') {
    try {
      const templateParams = {
        to_email: email,
        user_name: userName,
        otp_code: otp,
        otp_expiry: '10 minutes'
      }

      const response = await emailjs.send(
        SERVICE_ID,
        REGISTER_TEMPLATE_ID,
        templateParams
      )

      console.log('✅ Registration OTP email sent successfully via EmailJS:', response)
      return { success: true, message: 'OTP sent to your email' }
    } catch (error) {
      console.error('❌ Failed to send registration OTP email:', error)
      return {
        success: false,
        message: error.text || 'Failed to send OTP email. Please try again.'
      }
    }
  },

  async sendForgotPasswordOTP(email, otp, userName = 'User') {
    try {
      const templateParams = {
        to_email: email,
        user_name: userName,
        otp_code: otp,
        otp_expiry: '10 minutes'
      }

      const response = await emailjs.send(
        SERVICE_ID,
        FORGOT_PASSWORD_TEMPLATE_ID,
        templateParams
      )

      console.log('✅ Password reset OTP email sent successfully via EmailJS:', response)
      return { success: true, message: 'OTP sent to your email' }
    } catch (error) {
      console.error('❌ Failed to send password reset OTP email:', error)
      return {
        success: false,
        message: error.text || 'Failed to send OTP email. Please try again.'
      }
    }
  },

  // Generic method for flexibility
  async sendOTP(email, otp, userName = 'User', type = 'registration') {
    if (type === 'forgot-password') {
      return this.sendForgotPasswordOTP(email, otp, userName)
    }
    return this.sendRegistrationOTP(email, otp, userName)
  }
}

export default emailService
