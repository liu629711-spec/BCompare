p = r'D:\Rea\product\gui\WpfHost\MenuHost.cs'
s = open(p, encoding='utf-8').read()
old = """    internal sealed class BcMenuItemPeer : FrameworkElementAutomationPeer
    {
        public BcMenuItemPeer(BcMenuItem owner) : base(owner) { }

        protected override string GetNameCore()"""
new = """    internal sealed class BcMenuItemPeer : FrameworkElementAutomationPeer
    {
        public BcMenuItemPeer(BcMenuItem owner) : base(owner) { }

        // FrameworkElementAutomationPeer defaults these from the owner; state them
        // explicitly so the item stays in the control view (a peer that reports
        // IsControlElement=false is pruned — that is what dropped our items).
        protected override bool IsControlElementCore() => true;
        protected override AutomationControlType GetAutomationControlTypeCore()
            => AutomationControlType.MenuItem;
        protected override string GetClassNameCore() => "MenuItem";

        protected override string GetNameCore()"""
assert old in s, 'anchor missing'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('peer control-view members added')
