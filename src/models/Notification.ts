import mongoose, { Document, Schema } from 'mongoose';

export interface INotification extends Document {
  userId: mongoose.Types.ObjectId;
  title: string;
  message: string;
  notificationType: 'info' | 'warning' | 'success' | 'error';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  actionUrl?: string;
  expiresAt?: Date;
  extraData?: any;
  isRead: boolean;
  readAt?: Date;
  emailSent: boolean;
  emailSentAt?: Date;
  createdAt: Date;
}

const NotificationSchema = new Schema<INotification>({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  title: { type: String, required: true, maxlength: 200 },
  message: { type: String, required: true },
  notificationType: {
    type: String,
    enum: ['info', 'warning', 'success', 'error'],
    default: 'info'
  },
  priority: {
    type: String,
    enum: ['low', 'normal', 'high', 'urgent'],
    default: 'normal'
  },
  actionUrl: { type: String, maxlength: 500 },
  expiresAt: { type: Date },
  extraData: { type: Schema.Types.Mixed },
  isRead: { type: Boolean, default: false },
  readAt: { type: Date },
  emailSent: { type: Boolean, default: false },
  emailSentAt: { type: Date },
  createdAt: { type: Date, default: Date.now }
});

export default mongoose.model<INotification>('Notification', NotificationSchema);