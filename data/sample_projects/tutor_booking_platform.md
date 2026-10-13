# Stakeholder Requirements Specification (RFP)
## Project: University Peer Tutor Booking Platform
**Client:** University Academic Excellence Center
**Version:** 1.0 (Draft)

### 1. Executive Summary
The University Academic Excellence Center requires a modern digital platform to connect undergraduate and graduate students with peer tutors. The system must replace informal spreadsheet schedules and email bookings with a centralized, secure, and intuitive web application.

### 2. User Roles & Authentication
- Students and tutors shall authenticate using their institutional university credentials (.edu) with two-factor email verification.
- User accounts must maintain profile details, enrolled courses, and academic major.
- The platform should be secure and protect student privacy.

### 3. Tutor Discovery & Availability
- Students can search for tutors by course code (e.g., CS-101, MATH-204), topic, hourly rate, and peer rating.
- Tutors must manage their weekly availability through a recurring calendar scheduler.
- The platform should be fast under high student query traffic during midterms.

### 4. Booking & Session Management
- Students can view real-time open slots and reserve a 1-on-1 tutoring appointment.
- The system must prevent concurrent double-booking of any tutor's slot.
- Students can cancel a booking at any time without restriction and receive a full credit refund.

### 5. Policies & Financial Transactions
- All payments must be processed securely online before session confirmation.
- Important Policy Rule 4.2: To protect tutor commitment, bookings cannot be cancelled within 24 hours of scheduled session start.
- Tutors will receive bi-weekly automated payouts based on completed session logs.

### 6. Notifications & Administrative Governance
- Both tutor and student shall receive instant push and email notifications for booking confirmations, rescheduling, and reminders.
- University administrators shall monitor system telemetry, resolve student-tutor disputes, and inspect audit logs.
