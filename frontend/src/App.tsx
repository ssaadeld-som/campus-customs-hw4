import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import './auth.css'
import './chat-products.css'
import './chat-search-results.css'
import './size-chart.css'
import './usability.css'
import './design.css'
import './catalogue-filters.css'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type InventoryItem = { size: string; quantity: number }
type Product = { product_id: string; name: string; garment_type: string; description: string; colors: string[]; search_tags: string[]; image_file_path: string; image_url: string; price: number; inventory?: InventoryItem[]; total_stock?: number; available_sizes?: string[]; category?: string; customer_segment?: string }
type ChatProduct = Pick<Product, 'product_id' | 'name' | 'description' | 'image_url' | 'price' | 'total_stock'>
type ChatMessage = { role: 'user' | 'assistant'; content: string; products?: ChatProduct[] }
type Session = { token: string; user: { id: number; email: string; first_name: string | null } }

const money = (price: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price)
const productImage = (product: Pick<Product, 'image_url'>) => `${API_BASE}${product.image_url}`
const currentPageContext = () => { const path = window.location.pathname; const product = path.match(/^\/products\/([^/]+)$/); return { path, page_title: product ? 'Product detail' : path === '/products' ? 'Products' : path === '/about' ? 'About Us' : path === '/login' ? 'Log In' : path === '/create-account' ? 'Create Account' : 'Home', product_id: product?.[1] ?? null } }

const CHAT_SEARCH_KEY = 'campus-customs-chat-search'
const STOP_WORDS = new Set(['a', 'an', 'and', 'apparel', 'are', 'can', 'campus', 'customs', 'find', 'for', 'i', 'in', 'is', 'looking', 'me', 'of', 'please', 'search', 'show', 'the', 'to', 'what', 'with', 'yale', 'you'])
const SEARCH_ALIASES: Record<string, string> = { hoodies: 'hoodie', crewnecks: 'crewneck', sweaters: 'sweater', jackets: 'jacket', shirts: 'shirt', 't-shirts': 't-shirt', tshirts: 't-shirt', tees: 'tee', bottoms: 'bottom', pants: 'pant', shorts: 'short', products: 'product', items: 'item', womens: 'women', mens: 'men' }
const CATEGORY_TERMS: Record<string, string[]> = {
  'Tops & shirts': ['t-shirt', 't shirt', 'tee', 'shirt', 'long sleeve', 'polo', 'tank'],
  'Jackets & sweaters': ['hoodie', 'crewneck', 'sweater', 'fleece', 'jacket', 'zip', 'mockneck'],
  Activewear: ['activewear', 'baseball', 'basketball', 'crew', 'diving', 'fencing', 'field hockey', 'football', 'golf', 'hockey', 'lacrosse', 'sailing', 'soccer', 'squash', 'swimming', 'tennis', 'track', 'volleyball'],
  Bottoms: ['bottom', 'pant', 'short', 'legging', 'jogger'],
}
const SEGMENT_TERMS: Record<string, string[]> = {
  Youth: ['youth', 'kids', 'child'],
  Women: ['women', 'woman', 'mom', 'grandma', 'aunt'],
  Men: ['men', 'man', 'mens', "men's", 'dad', 'grandpa', 'uncle', 'brother'],
  Unisex: ['unisex'],
}

function productText(product: Product) {
  return [product.name, product.garment_type, product.description, product.colors.join(' '), product.search_tags.join(' '), product.category ?? '', product.customer_segment ?? ''].join(' ').toLowerCase()
}

function queryTerms(query: string) {
  return query.toLowerCase().replace(/[^a-z0-9-]+/g, ' ').split(/\s+/).map(term => SEARCH_ALIASES[term] ?? term).filter(term => term.length > 1 && !STOP_WORDS.has(term))
}

function matchesTerms(product: Product, terms: string[]) {
  const text = productText(product)
  return terms.every(term => text.includes(term))
}

function isCatalogueSearch(query: string, productsReturned: ChatProduct[]) {
  const inventoryIntent = /\b(stock|inventory|size|sizes|available|availability|how many|price|cost)\b/i.test(query)
  return productsReturned.length > 0 && !inventoryIntent && queryTerms(query).length > 0
}

function useProducts() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    fetch(`${API_BASE}/api/products`).then(response => response.ok ? response.json() : Promise.reject()).then(setProducts).catch(() => setError('The catalogue service is not running. Start the FastAPI server to load products.'))
  }, [])
  return { products, error }
}

function Header() {
  const path = window.location.pathname
  const links = [['Home', '/'], ['Products', '/products'], ['About Us', '/about'], ['Log In', '/login'], ['Create Account', '/create-account']]
  return <header className="site-header"><a className="wordmark" href="/" aria-label="Campus Customs home"><span>CC</span> Campus Customs</a><nav aria-label="Primary navigation">{links.map(([label, href]) => <a key={href} className={path === href ? 'active' : ''} href={href}>{label}</a>)}</nav></header>
}

function ProductCard({ product }: { product: Product }) {
  return <article className="product-card"><a href={`/products/${product.product_id}`} className="product-image-link"><img src={productImage(product)} alt={product.name} loading="lazy" /><span className="image-hover-note">View details <span aria-hidden="true">→</span></span></a><div className="product-card-copy"><p className="eyebrow">{product.garment_type}</p><div className="card-heading"><h3>{product.name}</h3><strong>{money(product.price)}</strong></div><p>{product.description}</p><a className="text-link" href={`/products/${product.product_id}`}>View item <span aria-hidden="true">→</span></a></div></article>
}

function Home({ products, error }: { products: Product[]; error: string }) {
  return <><section className="hero-section"><div className="hero-copy"><p className="eyebrow">New Haven, Connecticut</p><h1>Everyday gear for uncommon school spirit.</h1><p>Campus Customs brings a considered edit of Yale-inspired apparel to the moments that matter: game day, library day, and every day between.</p><a className="button" href="/products">Shop the collection <span aria-hidden="true">→</span></a></div><div className="hero-mark" aria-hidden="true"><span>C</span><span>C</span><p>EST. 2026<br />NEW HAVEN</p></div></section><section className="feature-strip"><p>Thoughtful layers</p><p>Campus classics</p><p>Made for showing up</p></section><section className="content-section"><div className="section-heading"><div><p className="eyebrow">The edit</p><h2>Start with a favorite.</h2></div><a className="text-link" href="/products">All products <span aria-hidden="true">→</span></a></div>{error ? <p className="notice">{error}</p> : <div className="product-grid featured-grid">{products.slice(0, 3).map(product => <ProductCard product={product} key={product.product_id} />)}</div>}</section><section className="story-banner"><p className="eyebrow">Campus Customs</p><h2>Designed for the long walk from Old Campus to wherever comes next.</h2><a href="/about" className="button button-light">Our story <span aria-hidden="true">→</span></a></section></>
}

function Products({ products, error, chatSearch, onClearChatSearch }: { products: Product[]; error: string; chatSearch: string; onClearChatSearch: () => void }) {
  const [category, setCategory] = useState('All'); const [segment, setSegment] = useState('All'); const [size, setSize] = useState('All'); const [availability, setAvailability] = useState('All'); const [color, setColor] = useState('All'); const [page, setPage] = useState(1)
  const categories = ['All', 'Tops & shirts', 'Jackets & sweaters', 'Activewear', 'Bottoms']; const segments = ['All', 'Youth', 'Men', 'Women', 'Unisex']; const sizes = ['All', 'XS', 'S', 'M', 'L', 'XL', 'XXL']; const colors = ['All', ...Array.from(new Set(products.flatMap(product => product.colors))).sort()]
  const searchTerms = queryTerms(chatSearch)
  const filtered = products.filter(product => {
    const text = productText(product)
    const categoryMatches = category === 'All' || product.category === category || (CATEGORY_TERMS[category] ?? []).some(term => text.includes(term))
    const segmentMatches = segment === 'All' || product.customer_segment === segment || (SEGMENT_TERMS[segment] ?? []).some(term => text.includes(term))
    const colorMatches = color === 'All' || text.includes(color.toLowerCase())
    const stockMatches = availability === 'All' || availability === 'In stock' && (product.total_stock ?? 0) > 0 || availability === 'Out of stock' && (product.total_stock ?? 0) === 0
    return categoryMatches && segmentMatches && (size === 'All' || product.available_sizes?.includes(size)) && stockMatches && colorMatches && matchesTerms(product, searchTerms)
  })
  const pageCount = Math.max(1, Math.ceil(filtered.length / 16)); const pageProducts = filtered.slice((page - 1) * 16, page * 16)
  function updateFilter(update: () => void) { update(); setPage(1) }
  return <main className="content-section products-page"><div className="page-intro"><p className="eyebrow">Campus Customs collection</p><h1>Wear the campus your way.</h1><p>Filter by category, customer segment, size, availability, or color—then browse 16 considered options at a time.</p></div>{error ? <p className="notice">{error}</p> : <>{chatSearch && <section className="chat-search-summary" aria-live="polite"><div><p className="eyebrow">Chat search applied</p><strong>Showing catalogue matches for “{chatSearch}”</strong></div><button type="button" onClick={onClearChatSearch}>Clear chat search ×</button></section>}<section className="catalogue-filters" aria-label="Product filters"><div className="filter-intro"><strong>Find your campus fit</strong><span>Mix filters with your chat search.</span></div><label>Category<select value={category} onChange={event => updateFilter(() => setCategory(event.target.value))}>{categories.map(value => <option key={value}>{value}</option>)}</select></label><label>Customer<select value={segment} onChange={event => updateFilter(() => setSegment(event.target.value))}>{segments.map(value => <option key={value}>{value}</option>)}</select></label><label>Size<select value={size} onChange={event => updateFilter(() => setSize(event.target.value))}>{sizes.map(value => <option key={value}>{value}</option>)}</select></label><label>Availability<select value={availability} onChange={event => updateFilter(() => setAvailability(event.target.value))}><option>All</option><option>In stock</option><option>Out of stock</option></select></label><label>Color<select value={color} onChange={event => updateFilter(() => setColor(event.target.value))}>{colors.map(value => <option key={value}>{value}</option>)}</select></label></section><p className="product-count">{filtered.length} matching items · Page {page} of {pageCount}</p><div className="product-grid">{pageProducts.map(product => <ProductCard product={product} key={product.product_id} />)}</div>{filtered.length === 0 && <p className="notice">No products match that combination. Clear a filter or try a broader chat search.</p>}<nav className="pagination" aria-label="Product pages"><button disabled={page === 1} onClick={() => setPage(page - 1)}>← Previous</button>{Array.from({ length: pageCount }, (_, index) => <button className={page === index + 1 ? 'current' : ''} onClick={() => setPage(index + 1)} key={index}>{index + 1}</button>)}<button disabled={page === pageCount} onClick={() => setPage(page + 1)}>Next →</button></nav></>}</main>
}

const SIZE_CHART = {
  Youth: [['YS', '26–27', '23–24', '27–28'], ['YM', '28–30', '24–25', '29–31'], ['YL', '30–32', '25–26', '31–33'], ['YXL', '32–34', '26–28', '33–35']],
  Women: [['XS', '32–33', '25–26', '34–35'], ['S', '34–35', '27–28', '36–37'], ['M', '36–37', '29–30', '38–39'], ['L', '38–40', '31–33', '40–42'], ['XL', '41–43', '34–36', '43–45']],
  Men: [['XS', '32–34', '27–29', '32–34'], ['S', '35–37', '29–31', '35–37'], ['M', '38–40', '32–34', '38–40'], ['L', '41–43', '35–37', '41–43'], ['XL', '44–46', '38–40', '44–46'], ['XXL', '48–50', '41–43', '48–50']],
} as const

function SizeChart() { return <section className="size-chart"><div><p className="eyebrow">Fit guide</p><h2>Find your everyday fit.</h2><p><strong>All measurements are body measurements in inches (in.).</strong> Use this US casual/activewear guide as a starting point; when a garment fit differs, use the product description and choose the larger size for a relaxed layer.</p></div><div className="size-chart-tables">{Object.entries(SIZE_CHART).map(([segment, rows]) => <div key={segment}><h3>{segment}</h3><table><thead><tr><th>Size</th><th>Chest / bust (in.)</th><th>Waist (in.)</th><th>Hip (in.)</th></tr></thead><tbody>{rows.map(row => <tr key={row[0]}>{row.map((cell, index) => <td key={index}>{cell}</td>)}</tr>)}</tbody></table></div>)}</div></section> }

function ProductDetail({ id }: { id: string }) {
  const [product, setProduct] = useState<Product | null>(null); const [error, setError] = useState(''); const [notifySize, setNotifySize] = useState(''); const [notifyEmail, setNotifyEmail] = useState(''); const [notifyStatus, setNotifyStatus] = useState('')
  useEffect(() => { fetch(`${API_BASE}/api/products/${id}`).then(r => r.ok ? r.json() : Promise.reject()).then(setProduct).catch(() => setError('We could not load this item. Make sure the FastAPI server is running.')) }, [id])
  if (error) return <main className="content-section"><p className="notice">{error}</p></main>
  if (!product) return <main className="content-section"><p className="loading">Loading product…</p></main>
  async function notify(event: FormEvent) { event.preventDefault(); setNotifyStatus(''); const response = await fetch(`${API_BASE}/api/stock-notifications`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: notifyEmail, product_id: product?.product_id, size: notifySize }) }); const data = await response.json(); setNotifyStatus(response.ok ? data.message : data.detail) }
  return <main className="content-section detail-page"><a className="back-link" href="/products">← Back to products</a><div className="product-detail"><div className="detail-image"><img src={productImage(product)} alt={product.name} /></div><div className="detail-copy"><p className="eyebrow">{product.garment_type}</p><h1>{product.name}</h1><p className="detail-price">{money(product.price)}</p><p className="detail-description">{product.description}</p><dl><div><dt>Colors</dt><dd>{product.colors.join(', ')}</dd></div><div><dt>Available sizes</dt><dd className="size-list">{product.inventory?.map(item => <span className={item.quantity > 0 ? 'in-stock' : 'sold-out'} key={item.size}>{item.size}</span>)}</dd></div><div><dt>Stock availability</dt><dd>{product.total_stock ?? 0} items across all sizes</dd></div></dl><div className="inventory-list">{product.inventory?.map(item => <div key={item.size}><span>{item.size}</span><span>{item.quantity > 0 ? `${item.quantity} in stock` : 'Sold out'}</span></div>)}</div>{product.inventory?.some(item => item.quantity === 0) && <form className="notify-form" onSubmit={notify}><p className="eyebrow">Back-in-stock email</p><p>Choose a sold-out size and we’ll save a one-time notification request.</p><select required value={notifySize} onChange={event => setNotifySize(event.target.value)}><option value="">Select sold-out size</option>{product.inventory?.filter(item => item.quantity === 0).map(item => <option key={item.size}>{item.size}</option>)}</select><input type="email" required value={notifyEmail} onChange={event => setNotifyEmail(event.target.value)} placeholder="you@example.com" aria-label="Email for stock notification" /><button className="button" type="submit">Notify me</button>{notifyStatus && <p className="form-status success" role="status">{notifyStatus}</p>}</form>}</div></div><SizeChart /></main>
}

function About() { return <main className="about-page"><section className="about-hero"><p className="eyebrow">About Campus Customs</p><h1>Well-made reminders of a place worth carrying with you.</h1></section><section className="about-grid"><div><h2>A school spirit shop, with more intention.</h2></div><div><p>Campus Customs is a fictional New Haven storefront shaped around the everyday rituals of campus life. Our collection pairs enduring collegiate colors with pieces that feel just as natural in a seminar as they do in the stands.</p><p>We believe school apparel can be personal, useful, and quietly distinctive. That is why every item starts with the details—fabric, fit, color, and the small marks that make a familiar place feel like your own.</p><a className="button" href="/products">Explore the collection <span aria-hidden="true">→</span></a></div></section></main> }

function AccountPage({ create, onLoggedIn }: { create: boolean; onLoggedIn: (session: Session) => void }) {
  const [status, setStatus] = useState(''); const [error, setError] = useState(''); const [sending, setSending] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setStatus(''); setError('')
    const fields = new FormData(event.currentTarget)
    const email = String(fields.get('email') ?? ''); const password = String(fields.get('password') ?? '')
    const confirmPassword = String(fields.get('confirmPassword') ?? '')
    if (create && password !== confirmPassword) { setError('Passwords do not match. Please re-enter both passwords.'); return }
    setSending(true)
    const body = create
      ? { first_name: String(fields.get('firstName') ?? ''), last_name: String(fields.get('lastName') ?? ''), email, password, confirm_password: confirmPassword }
      : { email, password }
    try {
      const response = await fetch(`${API_BASE}/api/auth/${create ? 'register' : 'login'}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      const data = await response.json()
      if (!response.ok) { setError(data.detail ?? 'Something went wrong. Please try again.'); return }
      setStatus(data.message); event.currentTarget.reset(); if (!create && data.session_token && data.user) onLoggedIn({ token: data.session_token, user: data.user })
    } catch { setError('We could not reach the account service. Please try again shortly.') } finally { setSending(false) }
  }
  return <main className="account-page"><section><p className="eyebrow">Campus Customs account</p><h1>{create ? 'Create your account' : 'Welcome back'}</h1><p>{create ? 'Save your preferences and pick up your shopping conversation whenever you return.' : 'Log in to continue your Campus Customs conversation.'}</p></section><form className="account-form" onSubmit={submit}>{create && <><label>First Name<input name="firstName" autoComplete="given-name" required /></label><label>Last Name<input name="lastName" autoComplete="family-name" required /></label></>}<label>Email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" autoComplete={create ? 'new-password' : 'current-password'} required /></label>{create && <label>Confirm Password<input name="confirmPassword" type="password" autoComplete="new-password" required /></label>}{error && <p className="form-status error" role="alert">{error}</p>}{status && <p className="form-status success" role="status">{status}</p>}<button className="button" type="submit" disabled={sending}>{sending ? 'Working…' : create ? 'Enter' : 'Log In'}</button>{create ? <p className="form-note">Already have an account? <a href="/login">Log In</a></p> : <p className="form-note">New to Campus Customs? <a href="/create-account">Create Account</a></p>}</form></main>
}

function ChatPanel({ onProductsReturned, sessionToken }: { onProductsReturned: (products: ChatProduct[], query: string) => void; sessionToken?: string }) {
  const [open, setOpen] = useState(false); const [input, setInput] = useState(''); const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'assistant', content: 'Hi! I can help you explore Campus Customs apparel.' }]); const [sending, setSending] = useState(false)
  useEffect(() => { if (!open || !sessionToken) return; fetch(`${API_BASE}/api/chat/history`, { headers: { Authorization: `Bearer ${sessionToken}` } }).then(response => response.ok ? response.json() : Promise.reject()).then(data => setMessages(data.messages)).catch(() => undefined) }, [open, sessionToken])
  async function submit(event: FormEvent) { event.preventDefault(); const message = input.trim(); if (!message || sending) return; setMessages(previous => [...previous, { role: 'user', content: message }]); setInput(''); setSending(true); try { const response = await fetch(`${API_BASE}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, session_token: sessionToken ?? null, page_context: currentPageContext() }) }); const data: { message?: string; detail?: string; products?: ChatProduct[] } = await response.json(); if (!response.ok) throw new Error(data.detail); const products = data.products ?? []; setMessages(previous => [...previous, { role: 'assistant', content: data.message ?? 'I could not form a reply.', products }]); onProductsReturned(products, message) } catch (error) { setMessages(previous => [...previous, { role: 'assistant', content: error instanceof Error && error.message ? error.message : 'I am having trouble reaching the shop assistant. Please try again shortly.' }]) } finally { setSending(false) } }
  return <aside className={`chat-widget ${open ? 'is-open' : ''}`}><button className="chat-launcher" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? '×' : '◌'} <span>{open ? 'Close' : 'Ask Campus Customs'}</span></button>{open && <section className="chat-panel" aria-label="Campus Customs chat"><header><p className="eyebrow">Campus Customs</p><h2>Shop assistant</h2></header><div className="chat-messages">{messages.map((message, index) => <div key={index} className={`message ${message.role}`}><p>{message.content}</p>{message.products?.map(product => <a className="chat-product" href={`/products/${product.product_id}`} key={product.product_id}><img src={productImage(product)} alt="" /><span><strong>{product.name}</strong><small>{money(product.price)} · {product.total_stock} in stock</small></span></a>)}</div>)}</div><form onSubmit={submit}><label className="sr-only" htmlFor="chat-input">Ask a question about merchandise</label><input id="chat-input" value={input} onChange={event => setInput(event.target.value)} placeholder="Ask about a hoodie, color, or sport…" /><button type="submit" disabled={sending}>{sending ? '…' : 'Send'}</button></form></section>}</aside>
}

function App() {
  const { products, error } = useProducts(); const [chatSearch, setChatSearch] = useState(() => sessionStorage.getItem(CHAT_SEARCH_KEY) ?? ''); const [session, setSession] = useState<Session | null>(() => { try { const value = localStorage.getItem('campus-customs-session'); return value ? JSON.parse(value) as Session : null } catch { return null } }); const path = window.location.pathname; const detailMatch = path.match(/^\/products\/([^/]+)$/)
  const storeSession = (next: Session) => { localStorage.setItem('campus-customs-session', JSON.stringify(next)); setSession(next) }
  const clearChatSearch = () => { sessionStorage.removeItem(CHAT_SEARCH_KEY); setChatSearch('') }
  const page = detailMatch ? <ProductDetail id={detailMatch[1]} /> : path === '/products' ? <Products key={chatSearch} products={products} error={error} chatSearch={chatSearch} onClearChatSearch={clearChatSearch} /> : path === '/about' ? <About /> : path === '/login' ? <AccountPage create={false} onLoggedIn={storeSession} /> : path === '/create-account' ? <AccountPage create onLoggedIn={storeSession} /> : <Home products={products} error={error} />
  return <><Header />{page}<footer><span>CC</span><p>Campus Customs · New Haven, Connecticut</p><a href="/about">About us</a></footer><ChatPanel sessionToken={session?.token} onProductsReturned={(results, query) => {
    if (!isCatalogueSearch(query, results)) return
    sessionStorage.setItem(CHAT_SEARCH_KEY, query)
    setChatSearch(query)
    if (window.location.pathname !== '/products') window.location.assign('/products')
  }} /></>
}
export default App
