import express from 'express';

const router = express.Router();

// Get all properties
router.get('/', async (req, res) => {
  try {
    res.json({ message: 'Properties endpoint - Coming soon' });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

export default router;