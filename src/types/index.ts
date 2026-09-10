export type Role = 'customer' | 'admin';

export interface User {
  id: string;
  email: string;
  mobile: string;
  fullName: string;
  avatarUrl?: string;
  role: Role;
  isActive: boolean;
  createdAt: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface LoginPayload {
  identifier: string; // email or mobile
  password: string;
}

export interface RegisterPayload {
  fullName: string;
  email: string;
  mobile: string;
  password: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  imageUrl: string;
  parentId?: string | null;
  sortOrder: number;
  itemCount?: number;
}

export interface ProductReview {
  id: string;
  productId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  rating: number;
  comment: string;
  createdAt: string;
}

export interface Product {
  id: string;
  slug: string;
  name: string;
  brand: string;
  categoryId: string;
  categoryName?: string;
  description: string;
  specifications: Record<string, string>;
  price: number;
  originalPrice: number;
  discountPercent: number;
  unit: string; // e.g. "500 g", "1 kg", "Pack of 2"
  stock: number;
  rating: number;
  ratingCount: number;
  images: string[];
  isPopular?: boolean;
  isFeatured?: boolean;
  isDeal?: boolean;
  tags: string[];
  inStock: boolean;
}

export interface CartItem {
  id: string;
  productId: string;
  product: Product;
  quantity: number;
}

export interface Cart {
  items: CartItem[];
  itemCount: number;
  subtotal: number;
  discount: number;
  deliveryFee: number;
  tax: number;
  total: number;
  appliedCoupon?: Coupon | null;
}

export type AddressType = 'home' | 'work' | 'other';

export interface Address {
  id: string;
  userId: string;
  fullName: string;
  mobile: string;
  houseFlat: string;
  street: string;
  area: string;
  city: string;
  state: string;
  pincode: string;
  landmark?: string;
  addressType: AddressType;
  isDefault: boolean;
}

export type AddressInput = Omit<Address, 'id' | 'userId'>;

export type OrderStatus =
  | 'order_placed'
  | 'confirmed'
  | 'preparing'
  | 'shipped'
  | 'out_for_delivery'
  | 'delivered'
  | 'cancelled';

export type PaymentStatus = 'pending' | 'paid' | 'failed' | 'refunded';

export type PaymentMethod = 'card' | 'upi' | 'netbanking' | 'cod';

export interface TrackingStep {
  status: OrderStatus;
  title: string;
  description: string;
  timestamp: string;
  completed: boolean;
  current: boolean;
}

export interface OrderItem {
  id: string;
  productId: string;
  productName: string;
  productImage: string;
  unitPrice: number;
  quantity: number;
  totalPrice: number;
  unit: string;
}

export interface Order {
  id: string;
  orderNumber: string;
  userId: string;
  address: Address;
  items: OrderItem[];
  subtotal: number;
  discount: number;
  deliveryFee: number;
  tax: number;
  total: number;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  paymentMethod: PaymentMethod;
  paymentTransactionId?: string;
  trackingHistory: TrackingStep[];
  deliverySlot?: string;
  estimatedDeliveryTime?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Coupon {
  id: string;
  code: string;
  discountType: 'percent' | 'fixed';
  discountValue: number;
  minOrderAmount: number;
  maxDiscount?: number;
  validUntil: string;
  description: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ProductFilters {
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  minRating?: number;
  brand?: string;
  inStock?: boolean;
  search?: string;
  sortBy?: 'relevance' | 'price_asc' | 'price_desc' | 'rating' | 'newest' | 'popular';
  page?: number;
  limit?: number;
}
