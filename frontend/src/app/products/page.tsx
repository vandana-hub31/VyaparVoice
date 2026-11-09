"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  Package,
  Plus,
  Search,
  AlertTriangle,
  Edit2,
  Trash2,
  CheckCircle2,
  X,
  Filter
} from "lucide-react";

export default function ProductsPage() {
  const { language } = useAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [lowStockFilter, setLowStockFilter] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<any>(null);

  // Form states
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [category, setCategory] = useState("General");
  const [unit, setUnit] = useState("pcs");
  const [costPrice, setCostPrice] = useState("");
  const [sellPrice, setSellPrice] = useState("");
  const [stock, setStock] = useState("");
  const [threshold, setThreshold] = useState("5");

  const t = translations[language] || translations.en;

  useEffect(() => {
    fetchProducts();
  }, [categoryFilter, lowStockFilter]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await api.getProducts({
        category: categoryFilter !== "All" ? categoryFilter : undefined,
        low_stock_only: lowStockFilter
      });
      setProducts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setEditingProduct(null);
    setName("");
    setSku("");
    setCategory("General");
    setUnit("pcs");
    setCostPrice("");
    setSellPrice("");
    setStock("");
    setThreshold("5");
    setShowAddModal(true);
  };

  const handleOpenEdit = (prod: any) => {
    setEditingProduct(prod);
    setName(prod.product_name);
    setSku(prod.SKU || "");
    setCategory(prod.category);
    setUnit(prod.unit);
    setCostPrice(prod.purchase_price);
    setSellPrice(prod.selling_price);
    setStock(prod.current_stock);
    setThreshold(prod.low_stock_threshold);
    setShowAddModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        product_name: name,
        SKU: sku || null,
        category,
        unit,
        purchase_price: Number(costPrice) || 0,
        selling_price: Number(sellPrice) || 0,
        current_stock: Number(stock) || 0,
        low_stock_threshold: Number(threshold) || 5
      };

      if (editingProduct) {
        await api.updateProduct(editingProduct.id, payload);
      } else {
        await api.createProduct(payload);
      }

      setShowAddModal(false);
      await fetchProducts();
    } catch (err: any) {
      alert(err?.message || "Failed to save product");
    }
  };

  const handleDelete = async (id: string, prodName: string) => {
    if (!confirm(`Are you sure you want to delete '${prodName}'?`)) return;
    try {
      await api.deleteProduct(id);
      await fetchProducts();
    } catch (err: any) {
      alert(err?.message || "Failed to delete product");
    }
  };

  const categories = ["All", ...Array.from(new Set(products.map((p) => p.category).filter(Boolean)))];

  const filtered = products.filter((p) =>
    p.product_name.toLowerCase().includes(search.toLowerCase()) ||
    (p.SKU && p.SKU.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t.products}</h1>
          <p className="text-xs text-slate-500">Manage shop inventory items, costs, and pricing</p>
        </div>

        <button
          onClick={handleOpenAdd}
          className="flex items-center gap-1.5 px-4 py-2 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl text-xs font-bold shadow-md shadow-vyapar-200 transition-all self-start sm:self-center"
        >
          <Plus className="w-4 h-4" />
          <span>{t.addProduct}</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 border border-slate-200 rounded-2xl shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by product name or SKU..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-vyapar-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-xl"
          >
            {categories.map((c) => (
              <option key={c} value={c}>
                Category: {c}
              </option>
            ))}
          </select>

          <button
            onClick={() => setLowStockFilter(!lowStockFilter)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border flex items-center gap-1.5 transition-colors ${
              lowStockFilter
                ? "bg-amber-500 text-white border-amber-600"
                : "bg-slate-50 text-slate-700 border-slate-300 hover:bg-slate-100"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Low Stock Only</span>
          </button>
        </div>
      </div>

      {/* Products Grid / Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Product Name</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4 text-right">Cost Price</th>
                <th className="py-3 px-4 text-right">Selling Price</th>
                <th className="py-3 px-4 text-right">Current Stock</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-400">
                    {loading ? "Loading catalog..." : "No products found."}
                  </td>
                </tr>
              ) : (
                filtered.map((p) => {
                  const isLowStock = Number(p.current_stock) <= Number(p.low_stock_threshold);
                  return (
                    <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-900 block">{p.product_name}</span>
                        {p.SKU && <span className="text-[10px] text-slate-400 font-mono">SKU: {p.SKU}</span>}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium text-[10px]">
                          {p.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-600">
                        ₹{Number(p.purchase_price).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-900">
                        ₹{Number(p.selling_price).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={`font-extrabold ${
                            isLowStock ? "text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md" : "text-slate-900"
                          }`}
                        >
                          {p.current_stock} {p.unit}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1">
                        <button
                          onClick={() => handleOpenEdit(p)}
                          className="p-1.5 text-slate-400 hover:text-slate-800 rounded-lg hover:bg-slate-100"
                          title="Edit Product"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(p.id, p.product_name)}
                          className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                          title="Delete Product"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Product Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white max-w-md w-full rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">
                {editingProduct ? "Edit Product" : "Add New Product"}
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Product Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Nandini Curd 500g"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="Dairy, Grains, etc."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Unit</label>
                  <select
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  >
                    <option value="pcs">Pieces (pcs)</option>
                    <option value="pkt">Packets (pkt)</option>
                    <option value="kg">Kilogram (kg)</option>
                    <option value="g">Gram (g)</option>
                    <option value="l">Litre (l)</option>
                    <option value="box">Box</option>
                    <option value="bag">Bag</option>
                    <option value="jar">Jar</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={costPrice}
                    onChange={(e) => setCostPrice(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Selling Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={sellPrice}
                    onChange={(e) => setSellPrice(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Current Stock</label>
                  <input
                    type="number"
                    step="0.01"
                    value={stock}
                    onChange={(e) => setStock(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Low Stock Alert Level</label>
                  <input
                    type="number"
                    step="0.01"
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    placeholder="5.00"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl font-bold"
                >
                  Save Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

