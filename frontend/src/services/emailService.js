import emailjs from '@emailjs/browser'

// Get credentials from environment variables
// Must use VITE_ prefix for frontend env vars in Vite
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY
const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID
const TEMPLATE_ID = import.meta.env.VITE_EMAILJS_TEMPLATE_ID

if (!PUBLIC_KEY || !SERVICE_ID || !TEMPLATE_ID) {
  console.warn('⚠️ Missing EmailJS configuration in .env file')
}

// Initialize EmailJS
emailjs.init(PUBLIC_KEY)

const emailService = {
  async sendOTP(email, otp, userName = 'User') {
    try {
      const templateParams = {
        to_email: email,
        user_name: userName,
        otp_code: otp,
        otp_expiry: '10 minutes'
      }

      const response = await emailjs.send(
        SERVICE_ID,
        TEMPLATE_ID,
        templateParams
      )

      console.log('✅ OTP email sent successfully via EmailJS:', response)
      return { success: true, message: 'OTP sent to your email' }
    } catch (error) {
      console.error('❌ Failed to send OTP email:', error)
      return {
        success: false,
        message: error.text || 'Failed to send OTP email. Please try again.'
      }
    }
  }
}

export default emailService
