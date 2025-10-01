import mongoose, { Document, Schema } from 'mongoose';

export interface IPayment extends Document {
  unitId: mongoose.Types.ObjectId;
  userId: mongoose.Types.ObjectId;
  amount: number;
  paymentType: 'maintenance' | 'penalty' | 'rent' | 'other';
  paymentMethod: 'cash' | 'transfer' | 'check' | 'card';
  paymentDate: Date;
  dueDate?: Date;
  description?: string;
  receiptNumber?: string;
  status: 'paid' | 'pending' | 'overdue';
  createdAt: Date;
}

const PaymentSchema = new Schema<IPayment>({
  unitId: { type: Schema.Types.ObjectId, ref: 'Unit', required: true },
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  amount: { type: Number, required: true },
  paymentType: {
    type: String,
    enum: ['maintenance', 'penalty', 'rent', 'other'],
    required: true
  },
  paymentMethod: {
    type: String,
    enum: ['cash', 'transfer', 'check', 'card'],
    default: 'cash'
  },
  paymentDate: { type: Date, required: true },
  dueDate: { type: Date },
  description: { type: String },
  receiptNumber: { type: String, unique: true },
  status: {
    type: String,
    enum: ['paid', 'pending', 'overdue'],
    default: 'paid'
  },
  createdAt: { type: Date, default: Date.now }
});

export default mongoose.model<IPayment>('Payment', PaymentSchema);