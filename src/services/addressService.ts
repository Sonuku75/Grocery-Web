import { apiClient } from "@/lib/api";
import { Address, AddressInput } from "@/types";
import { MOCK_ADDRESSES } from "@/lib/mockData";

const STORAGE_KEY = "cartify_addresses";

export const addressService = {
  getStoredAddresses(): Address[] {
    if (typeof window === "undefined") return MOCK_ADDRESSES;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(MOCK_ADDRESSES));
      return MOCK_ADDRESSES;
    }
    try {
      return JSON.parse(stored) as Address[];
    } catch {
      return MOCK_ADDRESSES;
    }
  },

  saveStoredAddresses(addresses: Address[]) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(addresses));
  },

  async getAddresses(): Promise<Address[]> {
    const res = await apiClient.get<Address[]>("/addresses");
    if (res.success && res.data && res.data.length > 0) {
      this.saveStoredAddresses(res.data);
      return res.data;
    }
    return this.getStoredAddresses();
  },

  async addAddress(input: AddressInput): Promise<Address> {
    const res = await apiClient.post<Address>("/addresses", input);
    if (res.success && res.data) {
      const current = this.getStoredAddresses();
      this.saveStoredAddresses([res.data, ...current]);
      return res.data;
    }

    const current = this.getStoredAddresses();
    const newAddress: Address = {
      ...input,
      id: "addr-" + Date.now(),
      userId: "usr-demo",
      isDefault: input.isDefault || current.length === 0,
    };

    let updated = [newAddress, ...current];
    if (newAddress.isDefault) {
      updated = updated.map((a) => (a.id === newAddress.id ? a : { ...a, isDefault: false }));
    }
    this.saveStoredAddresses(updated);
    return newAddress;
  },

  async updateAddress(id: string, input: Partial<AddressInput>): Promise<Address> {
    const res = await apiClient.put<Address>(`/addresses/${id}`, input);
    if (res.success && res.data) {
      const current = this.getStoredAddresses();
      const updated = current.map((a) => (a.id === id ? res.data : a));
      this.saveStoredAddresses(updated);
      return res.data;
    }

    const current = this.getStoredAddresses();
    let updated = current.map((a) => (a.id === id ? { ...a, ...input } : a));
    if (input.isDefault) {
      updated = updated.map((a) => (a.id === id ? { ...a, isDefault: true } : { ...a, isDefault: false }));
    }
    this.saveStoredAddresses(updated);
    return updated.find((a) => a.id === id)!;
  },

  async deleteAddress(id: string): Promise<boolean> {
    await apiClient.delete(`/addresses/${id}`);
    const current = this.getStoredAddresses();
    const updated = current.filter((a) => a.id !== id);
    if (updated.length > 0 && !updated.some((a) => a.isDefault)) {
      updated[0].isDefault = true;
    }
    this.saveStoredAddresses(updated);
    return true;
  },

  async setDefaultAddress(id: string): Promise<Address[]> {
    await apiClient.put(`/addresses/${id}/default`);
    const current = this.getStoredAddresses();
    const updated = current.map((a) => ({ ...a, isDefault: a.id === id }));
    this.saveStoredAddresses(updated);
    return updated;
  },
};
