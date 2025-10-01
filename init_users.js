const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

// Conectar a MongoDB
const MONGO_URI = 'mongodb+srv://geopublicidad507_db_user:Cdeg14650641*@consultor351.yv7gbsp.mongodb.net/miDB?retryWrites=true&w=majority';

// Esquema de Usuario
const UserSchema = new mongoose.Schema({
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

const User = mongoose.model('User', UserSchema);

// Usuarios iniciales
const initialUsers = [
  // Administradores Generales
  {
    email: 'admin@phcontrol.com',
    firstName: 'Administrador',
    lastName: 'General',
    phone: '+507 6000-0001',
    password: 'admin123',
    role: 'admin_general'
  },
  {
    email: 'superadmin@phcontrol.com',
    firstName: 'Super',
    lastName: 'Administrador',
    phone: '+507 6000-0002',
    password: 'super123',
    role: 'admin_general'
  },
  // Administradores de PH
  {
    email: 'adminph1@phcontrol.com',
    firstName: 'Carlos',
    lastName: 'Rodríguez',
    phone: '+507 6100-0001',
    password: 'adminph123',
    role: 'admin_ph'
  },
  {
    email: 'adminph2@phcontrol.com',
    firstName: 'María',
    lastName: 'González',
    phone: '+507 6100-0002',
    password: 'adminph123',
    role: 'admin_ph'
  },
  // Residentes
  {
    email: 'residente1@phcontrol.com',
    firstName: 'Ana',
    lastName: 'López',
    phone: '+507 6200-0001',
    password: 'resident123',
    role: 'resident'
  },
  {
    email: 'residente2@phcontrol.com',
    firstName: 'Pedro',
    lastName: 'Sánchez',
    phone: '+507 6200-0002',
    password: 'resident123',
    role: 'resident'
  }
];

async function initUsers() {
  try {
    console.log('🔌 Conectando a MongoDB...');
    await mongoose.connect(MONGO_URI);
    console.log('✅ Conectado a MongoDB');

    // Limpiar usuarios existentes
    await User.deleteMany({});
    console.log('🗑️ Usuarios existentes eliminados');

    // Crear usuarios
    for (const userData of initialUsers) {
      const salt = await bcrypt.genSalt(10);
      const passwordHash = await bcrypt.hash(userData.password, salt);
      
      const user = new User({
        email: userData.email,
        firstName: userData.firstName,
        lastName: userData.lastName,
        phone: userData.phone,
        passwordHash: passwordHash,
        role: userData.role
      });

      await user.save();
      console.log(`✅ Usuario creado: ${userData.email} (${userData.role})`);
    }

    console.log('🎉 Todos los usuarios han sido creados exitosamente');
    
    // Verificar usuarios creados
    const userCount = await User.countDocuments();
    console.log(`📊 Total de usuarios en la base de datos: ${userCount}`);

    process.exit(0);
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

initUsers();