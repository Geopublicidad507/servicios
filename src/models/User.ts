import mongoose, { Document, Schema } from 'mongoose';
import bcrypt from 'bcryptjs';

export interface IUser extends Document {
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  passwordHash: string;
  role: 'admin_general' | 'admin_ph' | 'resident' | 'provider' | 'visitor';
  isActive: boolean;
  createdAt: Date;
  lastLogin?: Date;
  comparePassword(password: string): Promise<boolean>;
}

const UserSchema = new Schema<IUser>({
  email: { type: String, required: true, unique: true },
  firstName: { type: String, required: true },
  lastName: { type: String, required: true },
  phone: { type: String },
  passwordHash: { type: String, required: true },
  role: { 
    type: String, 
    enum: ['admin_general', 'admin_ph', 'resident', 'provider', 'visitor'],
    default: 'resident'
  },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  lastLogin: { type: Date }
});

UserSchema.methods.comparePassword = async function(password: string): Promise<boolean> {
  return bcrypt.compare(password, this.passwordHash);
};

UserSchema.pre('save', async function(next) {
  if (!this.isModified('passwordHash')) return next();
  
  const salt = await bcrypt.genSalt(10);
  this.passwordHash = await bcrypt.hash(this.passwordHash, salt);
  next();
});

export default mongoose.model<IUser>('User', UserSchema);