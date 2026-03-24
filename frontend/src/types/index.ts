// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_email_verified: boolean;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// ─── Categories ──────────────────────────────────────────────────────────────

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  image: string | null;
  parent: number | null;
  children: Category[];
  product_count: number;
}

// ─── Products ────────────────────────────────────────────────────────────────

export type ProductType = 'physical' | 'digital' | 'bundle';

export interface ProductImage {
  id: number;
  image: string;
  alt_text: string;
  is_primary: boolean;
  order: number;
}

export interface ProductSpec {
  label: string;
  value: string;
}

export interface ProductListItem {
  id: number;
  slug: string;
  title: string;
  price: string;
  compare_at_price: string | null;
  primary_image: ProductImage | null;
  skill_tags: string[];
  product_type: ProductType;
  format_specs: ProductSpec[];
  is_in_stock: boolean;
  category: { id: number; name: string; slug: string };
  short_description: string;
}

export interface ProductDetail extends ProductListItem {
  description: string;
  images: ProductImage[];
  specs: ProductSpec[];
  weight_grams: number | null;
  sku_set: ProductSKU[];
  related_products: ProductListItem[];
  meta_title: string;
  meta_description: string;
  created_at: string;
  updated_at: string;
}

export interface ProductSKU {
  id: number;
  sku_code: string;
  attributes: Record<string, string>;
  price: string;
  stock_quantity: number;
  is_available: boolean;
}

// ─── Cart ─────────────────────────────────────────────────────────────────────

export interface CartItem {
  id: number;
  sku: ProductSKU & { product: Pick<ProductListItem, 'id' | 'slug' | 'title' | 'primary_image'> };
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface Cart {
  token: string;
  items: CartItem[];
  subtotal: string;
  item_count: number;
}

// ─── Address ──────────────────────────────────────────────────────────────────

export interface Address {
  id: number;
  first_name: string;
  last_name: string;
  company: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;
  phone: string;
  is_default: boolean;
}

export interface AddressPayload {
  first_name: string;
  last_name: string;
  company?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;
  phone?: string;
  is_default?: boolean;
}

// ─── Checkout ─────────────────────────────────────────────────────────────────

export interface ShippingMethod {
  id: string;
  name: string;
  description: string;
  price: string;
  estimated_days_min: number;
  estimated_days_max: number;
}

export interface TaxEstimate {
  tax_rate: string;
  tax_amount: string;
  jurisdiction: string;
}

export interface CheckoutRequest {
  cart_token: string;
  contact_email: string;
  contact_phone?: string;
  shipping_address: AddressPayload;
  billing_address?: AddressPayload;
  billing_same_as_shipping: boolean;
  shipping_method_id: string;
  payment_method_nonce: string;
  coupon_code?: string;
}

export interface CheckoutSession {
  token: string;
  cart_token: string;
  contact_email: string;
  contact_phone: string;
  shipping_address: Address | null;
  billing_address: Address | null;
  billing_same_as_shipping: boolean;
  shipping_method: ShippingMethod | null;
  subtotal: string;
  shipping_total: string;
  tax_total: string;
  grand_total: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
}

// ─── Orders ───────────────────────────────────────────────────────────────────

export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded',
}

export interface OrderLineItem {
  id: number;
  product_title: string;
  sku_code: string;
  sku_attributes: Record<string, string>;
  quantity: number;
  unit_price: string;
  line_total: string;
  product_image: string | null;
}

export interface OrderSummary {
  id: number;
  order_number: string;
  status: OrderStatus;
  created_at: string;
  item_count: number;
  subtotal: string;
  shipping_total: string;
  tax_total: string;
  grand_total: string;
}

export interface Order extends OrderSummary {
  items: OrderLineItem[];
  contact_email: string;
  contact_phone: string;
  shipping_address: Address;
  billing_address: Address;
  shipping_method: ShippingMethod;
  tracking_number: string | null;
  tracking_url: string | null;
  notes: string;
  updated_at: string;
}

// ─── Account ──────────────────────────────────────────────────────────────────

export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  is_email_verified: boolean;
  date_joined: string;
  default_shipping_address: Address | null;
}

export interface ProfileUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone?: string;
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchResponse {
  query: string;
  results: ProductListItem[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Shared ───────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface APIError {
  status: number;
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
}
