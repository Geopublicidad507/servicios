import mongoose, { Document, Schema } from 'mongoose';

export interface ITicket extends Document {
  userId: mongoose.Types.ObjectId;
  title: string;
  description: string;
  category: 'maintenance' | 'complaint' | 'request' | 'suggestion';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  assignedTo?: mongoose.Types.ObjectId;
  resolution?: string;
  createdAt: Date;
  updatedAt: Date;
}

const TicketSchema = new Schema<ITicket>({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  title: { type: String, required: true, maxlength: 200 },
  description: { type: String, required: true },
  category: {
    type: String,
    enum: ['maintenance', 'complaint', 'request', 'suggestion'],
    required: true
  },
  priority: {
    type: String,
    enum: ['low', 'medium', 'high', 'urgent'],
    default: 'medium'
  },
  status: {
    type: String,
    enum: ['open', 'in_progress', 'resolved', 'closed'],
    default: 'open'
  },
  assignedTo: { type: Schema.Types.ObjectId, ref: 'User' },
  resolution: { type: String },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

// Update the updatedAt field before saving
TicketSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

export default mongoose.model<ITicket>('Ticket', TicketSchema);