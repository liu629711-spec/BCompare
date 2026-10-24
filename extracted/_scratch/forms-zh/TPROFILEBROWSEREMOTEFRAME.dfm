object ProfileBrowseRemoteFrame: TProfileBrowseRemoteFrame
  Left = 0
  Top = 0
  Width = 424
  Height = 511
  TabOrder = 0
  object TreeView: TUiTreeView
    Left = 0
    Top = 0
    Width = 424
    Height = 511
    Align = alClient
    ReadOnly = True
    TabOrder = 0
    OnChange = TreeViewChange
    OnCollapsed = TreeViewCollapsed
    OnCollapsing = TreeViewCollapsing
    OnDeletion = TreeViewDeletion
    OnExpanding = TreeViewExpanding
  end
end
